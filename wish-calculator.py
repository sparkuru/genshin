# -*- coding: utf-8 -*-
# Genshin Impact wish calculator.
# Gacha modeling ported from https://github.com/OneBST/GGanalysis
# Single file, numpy-only (scipy convolution/FFT replaced by numpy.convolve).

import sys
import argparse
from typing import Union

import numpy as np

DEBUG_MODE = False

# Default demo scenario, used when running with --demo.
# One UP character (10 pity, no guarantee) plus one fate-bound weapon, 180 fates.
DEFAULT_DEMO_CONFIG = {
    "fates": 180,
    "target_characters": 1,
    "char_pity": 10,
    "char_guaranteed": False,
    "cr_counter": 1,
    "target_weapons": 1,
    "weapon_pity": 0,
    "weapon_guaranteed": False,
    "fate_point": 1,
}


class CLIStyle:
    """CLI tool unified style config."""

    COLORS = {
        "TITLE": 7,
        "SUB_TITLE": 2,
        "CONTENT": 3,
        "EXAMPLE": 7,
        "WARNING": 4,
        "ERROR": 2,
    }

    @staticmethod
    def color(text: str = "", color: int = COLORS["CONTENT"]) -> str:
        """Unified color processing function."""
        color_table = {
            0: "{}",
            1: "\033[1;30m{}\033[0m",
            2: "\033[1;31m{}\033[0m",
            3: "\033[1;32m{}\033[0m",
            4: "\033[1;33m{}\033[0m",
            5: "\033[1;34m{}\033[0m",
            6: "\033[1;35m{}\033[0m",
            7: "\033[1;36m{}\033[0m",
            8: "\033[1;37m{}\033[0m",
        }
        return color_table[color].format(text)


class ColoredArgumentParser(argparse.ArgumentParser):
    """Argument parser with colorized help output."""

    def _format_action_invocation(self, action: argparse.Action) -> str:
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest)(1)
            return metavar
        parts = []
        if action.nargs == 0:
            parts.extend(
                CLIStyle.color(x, CLIStyle.COLORS["SUB_TITLE"])
                for x in action.option_strings
            )
        else:
            args_string = self._format_args(action, action.dest.upper())
            for option_string in action.option_strings:
                parts.append(
                    CLIStyle.color(
                        f"{option_string} {args_string}",
                        CLIStyle.COLORS["SUB_TITLE"],
                    )
                )
        return ", ".join(parts)

    def format_help(self) -> str:
        formatter = self._get_formatter()
        if self.description:
            formatter.add_text(
                CLIStyle.color(self.description, CLIStyle.COLORS["TITLE"])
            )
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)
        formatter.add_text(CLIStyle.color("\n可选参数：", CLIStyle.COLORS["TITLE"]))
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()
        if self.epilog:
            formatter.add_text(self.epilog)
        return formatter.format_help()


def create_example_text(
    script_name: str, examples: list, notes: Union[list, None] = None
) -> str:
    """Build a colorized examples/notes epilog block for argparse help."""
    text = f"\n{CLIStyle.color('示例：', CLIStyle.COLORS['SUB_TITLE'])}"
    for desc, cmd in examples:
        text += f"\n  {CLIStyle.color(f'# {desc}', CLIStyle.COLORS['EXAMPLE'])}"
        text += f"\n  {CLIStyle.color(f'{script_name} {cmd}', CLIStyle.COLORS['CONTENT'])}\n"
    if notes:
        text += f"\n{CLIStyle.color('说明：', CLIStyle.COLORS['SUB_TITLE'])}"
        for note in notes:
            text += f"\n  {CLIStyle.color(f'- {note}', CLIStyle.COLORS['CONTENT'])}"
    return text


def pad_zero(dist: np.ndarray, target_len: int) -> np.ndarray:
    """Pad a numpy array with trailing zeros up to target_len."""
    if target_len <= len(dist):
        return dist
    return np.pad(dist, (0, target_len - len(dist)), "constant", constant_values=0)


def calc_expectation(dist: Union["FiniteDist", list, np.ndarray]) -> float:
    """Expectation of a discrete distribution over natural-number positions."""
    if isinstance(dist, FiniteDist):
        dist = dist.dist
    else:
        dist = np.asarray(dist, dtype=float)
    x = np.arange(len(dist))
    return float(np.dot(x, dist))


def calc_variance(dist: Union["FiniteDist", list, np.ndarray]) -> float:
    """Variance of a discrete distribution over natural-number positions."""
    if isinstance(dist, FiniteDist):
        dist = dist.dist
    else:
        dist = np.asarray(dist, dtype=float)
    x = np.arange(len(dist), dtype=np.float64)
    ex = float(np.dot(x, dist))
    ex2 = float(np.dot(x * x, dist))
    var = ex2 - ex * ex
    return var if var > 0.0 else 0.0


def p2dist(pity_p: Union[list, np.ndarray]) -> "FiniteDist":
    """Convert a pity probability table into a draw-count distribution."""
    pity_p = np.asarray(pity_p, dtype=float)
    dist = np.zeros(len(pity_p), dtype=float)
    temp = 1.0
    for i in range(1, len(pity_p)):
        dist[i] = temp * pity_p[i]
        temp *= 1 - pity_p[i]
    return FiniteDist(dist)


def cut_dist(
    dist: Union[np.ndarray, "FiniteDist"], cut_pos: int
) -> Union[np.ndarray, "FiniteDist"]:
    """Cut off the head of a distribution at cut_pos and renormalize."""
    if cut_pos == 0:
        return dist
    ans = dist[cut_pos:].copy()
    ans[0] = 0
    return ans / np.sum(ans)


class FiniteDist:
    """
    Finite-length 1D discrete distribution.

    Wraps a numpy array. ``*`` between two FiniteDist is convolution (sum of
    random variables); ``*`` with a scalar is element scaling; ``+`` adds two
    distributions aligned at position 0; ``** n`` is n-fold self convolution.
    ``exp`` / ``var`` / ``p_sum`` / ``cdf`` are computed lazily on access.
    ```python
    FiniteDist([0.5, 0.5]) * FiniteDist([0, 1])

    return = FiniteDist
    ```
    """

    def __init__(
        self,
        dist: Union[list, np.ndarray, "FiniteDist", None] = None,
        trim_tail_zeros: bool = True,
    ) -> None:
        if dist is None:
            dist = [1.0]
        if isinstance(dist, FiniteDist):
            self._dist = np.array(dist.dist, dtype=float)
            return
        arr = np.array(dist, dtype=float)
        if arr.ndim != 1:
            raise ValueError("Not a 1D distribution.")
        if trim_tail_zeros:
            arr = np.trim_zeros(arr, "b")
        if arr.size == 0:
            arr = np.zeros(1, dtype=float)
        self._dist = arr

    @property
    def dist(self) -> np.ndarray:
        """Read-only view of the underlying distribution array."""
        view = self._dist.view()
        view.flags.writeable = False
        return view

    def __getattr__(self, key: str):
        if key in ("exp", "var", "p_sum"):
            self._calc_moments()
            return self.__dict__[key]
        if key == "cdf":
            cdf = np.cumsum(self._dist)
            self.__dict__["cdf"] = cdf
            return cdf
        raise AttributeError(key)

    def _calc_moments(self, p_error: float = 1e-6) -> None:
        """Compute and cache p_sum, exp and var. exp/var are nan if p_sum != 1."""
        p_sum = float(np.sum(self._dist))
        self.__dict__["p_sum"] = p_sum
        if abs(p_sum - 1) > p_error:
            self.__dict__["exp"] = float("nan")
            self.__dict__["var"] = float("nan")
            return
        x = np.arange(len(self._dist), dtype=float)
        exp = float(np.dot(x, self._dist))
        self.__dict__["exp"] = exp
        self.__dict__["var"] = float(np.dot((x - exp) ** 2, self._dist))

    def __getitem__(self, sliced):
        return self._dist[sliced].copy()

    def __setitem__(self, sliced, value: Union[int, float, np.ndarray]) -> None:
        self._dist[sliced] = value
        for key in ("exp", "var", "p_sum", "cdf"):
            self.__dict__.pop(key, None)

    def __len__(self) -> int:
        return len(self._dist)

    def __iter__(self):
        return iter(self._dist)

    def __add__(self, other: "FiniteDist") -> "FiniteDist":
        target_len = max(len(self), len(other))
        return FiniteDist(
            pad_zero(self._dist, target_len) + pad_zero(other._dist, target_len)
        )

    def __mul__(self, other: Union["FiniteDist", float, int]) -> "FiniteDist":
        if isinstance(other, FiniteDist):
            return FiniteDist(np.convolve(self._dist, other._dist))
        return FiniteDist(self._dist * other)

    def __rmul__(self, other: Union["FiniteDist", float, int]) -> "FiniteDist":
        return self * other

    def __truediv__(self, other: Union[float, int]) -> "FiniteDist":
        return FiniteDist(self._dist / other)

    def __pow__(self, pow_times: int) -> "FiniteDist":
        if not isinstance(pow_times, int) or pow_times < 0:
            raise ValueError("pow_times must be a non-negative integer")
        result = np.ones(1, dtype=float)
        base = self._dist.copy()
        while pow_times > 0:
            if pow_times & 1:
                result = np.convolve(result, base)
            pow_times >>= 1
            if pow_times > 0:
                base = np.convolve(base, base)
        return FiniteDist(result)

    def __str__(self) -> str:
        return f"finite 1D dist {self._dist}"


class GachaLayer:
    """Base gacha layer; a callable returns (full_dist, conditional_dist)."""

    def __init__(self) -> None:
        self.dist = FiniteDist([1])
        self.exp = 0.0
        self.var = 0.0

    def __call__(self, input_dist=None, *args, **kwds) -> tuple:
        return self._forward(input_dist, 1), self._forward(input_dist, 0, *args, **kwds)

    def _forward(self, input_dist, full_mode: int, *args, **kwds) -> FiniteDist:
        raise NotImplementedError


class PityLayer(GachaLayer):
    """Pity layer; chains an inner per-item distribution into a compound one."""

    def __init__(self, pity_info: Union[list, np.ndarray, FiniteDist]) -> None:
        super().__init__()
        if isinstance(pity_info, FiniteDist):
            self.dist = pity_info
        else:
            self.pity_p = np.asarray(pity_info, dtype=float)
            self.dist = p2dist(self.pity_p)
        self.exp = self.dist.exp
        self.var = self.dist.var

    def _forward(self, input_dist, full_mode: int, item_pity: int = 0) -> FiniteDist:
        if input_dist is None:
            return FiniteDist(cut_dist(self.dist, item_pity))
        f_dist: FiniteDist = input_dist[0]
        c_dist: FiniteDist = input_dist[0] if full_mode else input_dist[1]
        overlay_dist = FiniteDist(cut_dist(self.dist, item_pity))
        output_dist = FiniteDist([0])
        output_e = 0.0
        output_d = 0.0
        temp_dist = FiniteDist([1])
        output_dist += float(overlay_dist[0]) * temp_dist
        for i in range(1, len(overlay_dist)):
            c_i = float(overlay_dist[i])
            output_dist += c_i * (c_dist * temp_dist)
            temp_dist = temp_dist * f_dist
            output_e += c_i * (c_dist.exp + (i - 1) * f_dist.exp)
            output_d += c_i * (
                c_dist.var
                + (i - 1) * f_dist.var
                + (c_dist.exp + (i - 1) * f_dist.exp) ** 2
            )
        output_d -= output_e**2
        output_dist.exp = output_e
        output_dist.var = output_d
        return output_dist


class GachaModel:
    """Base class for all gacha models."""

    pass


class CommonGachaModel(GachaModel):
    """Layered gacha model where obtaining each item is an independent event."""

    def __init__(self) -> None:
        super().__init__()
        self.layers: list = []

    def __call__(
        self, item_num: int = 1, multi_dist: bool = False, *args, **kwds
    ) -> Union[FiniteDist, list]:
        parameter_list = self._build_parameter_list(*args, **kwds)
        if item_num == 0:
            return FiniteDist([1])
        if multi_dist:
            return self._get_multi_dist(item_num, parameter_list)
        return self._get_dist(item_num, parameter_list)

    def _build_parameter_list(self, *args, **kwds) -> list:
        return [[[], {}] for _ in self.layers]

    def _get_multi_dist(self, end_pos: int, parameter_list: list) -> list:
        input_dist = self._forward(parameter_list)
        ans_list = [FiniteDist([1]), input_dist[1]]
        for i in range(1, end_pos):
            ans_list.append(ans_list[i] * input_dist[0])
            ans_list[i + 1].exp = input_dist[1].exp + input_dist[0].exp * i
            ans_list[i + 1].var = input_dist[1].var + input_dist[0].var * i
        return ans_list

    def _get_dist(self, item_num: int, parameter_list: list) -> FiniteDist:
        ans_dist = self._forward(parameter_list)
        ans: FiniteDist = ans_dist[1] * ans_dist[0] ** (item_num - 1)
        ans.exp = ans_dist[1].exp + ans_dist[0].exp * (item_num - 1)
        ans.var = ans_dist[1].var + ans_dist[0].var * (item_num - 1)
        return ans

    def _forward(self, parameter_list: Union[list, None] = None):
        ans_dist = None
        if parameter_list is None:
            for layer in self.layers:
                ans_dist = layer(ans_dist)
            return ans_dist
        for parameter, layer in zip(parameter_list, self.layers):
            ans_dist = layer(ans_dist, *parameter[0], **parameter[1])
        return ans_dist


class PityModel(CommonGachaModel):
    """Single pity model."""

    def __init__(self, pity_p) -> None:
        super().__init__()
        self.layers.append(PityLayer(pity_p))

    def __call__(
        self, item_num: int = 1, multi_dist: bool = False, item_pity: int = 0
    ) -> Union[FiniteDist, list]:
        return super().__call__(item_num, multi_dist, item_pity)

    def _build_parameter_list(self, item_pity: int = 0) -> list:
        return [[[], {"item_pity": item_pity}]]


class DualPityModel(CommonGachaModel):
    """Two-stage pity model (item pity followed by an up pity)."""

    def __init__(self, pity_p1, pity_p2) -> None:
        super().__init__()
        self.layers.append(PityLayer(pity_p1))
        self.layers.append(PityLayer(pity_p2))

    def __call__(
        self,
        item_num: int = 1,
        multi_dist: bool = False,
        item_pity: int = 0,
        up_pity: int = 0,
    ) -> Union[FiniteDist, list]:
        return super().__call__(item_num, multi_dist, item_pity, up_pity)

    def _build_parameter_list(self, item_pity: int = 0, up_pity: int = 0) -> list:
        return [
            [[], {"item_pity": item_pity}],
            [[], {"item_pity": up_pity}],
        ]


def capturing_radiance_dp(
    item_num: int = 1,
    up_pity: int = 0,
    cr_count: int = 1,
    cr_p: Union[list, None] = None,
) -> np.ndarray:
    """
    Distribution of the number of 5-stars consumed to obtain item_num UP
    5-stars under the Capturing Radiance counter mechanism.
    ```python
    capturing_radiance_dp(item_num=2, up_pity=0, cr_count=1)

    return = np.ndarray
    ```
    """
    if cr_p is None:
        cr_p = CR_P
    cr = np.asarray(cr_p, dtype=float)
    max_5star = (item_num // 3 * 5) + item_num % 3 * 2 + int(cr_count == 0)
    matrix = np.zeros((max_5star + 1, item_num + 1, 4), dtype=float)
    matrix[up_pity, up_pity, cr_count] = 1
    for i in range(1, max_5star + 1):
        for j in range(1, item_num + 1):
            if i >= 2:
                matrix[i, j, 1:4] += matrix[i - 2, j - 1, 0:3] * (0.5 - cr[0:3] / 2)
            matrix[i, j, 0:2] += matrix[i - 1, j - 1, 1:3] * (0.5 - cr[1:3] / 2)
            matrix[i, j, 0] += matrix[i - 1, j - 1, 0] * (0.5 - cr[0] / 2)
            matrix[i, j, 1] += matrix[i - 1, j - 1, 0:4] @ cr
    return np.trim_zeros(np.sum(matrix[:, item_num, :], axis=1), "b")


class CapturingRadianceModel(GachaModel):
    """Genshin character UP model with the 5.0+ Capturing Radiance mechanism."""

    def __init__(self, pity5_p=None, cr_p=None) -> None:
        if pity5_p is None:
            pity5_p = PITY_5STAR
        if cr_p is None:
            cr_p = CR_P
        self.common_5star = PityModel(pity5_p)
        self.cr_p = cr_p

    def _get_cr_5star_dist(
        self, item_num: int, up_pity: int = 0, cr_counter: int = 0
    ) -> FiniteDist:
        return FiniteDist(
            capturing_radiance_dp(item_num, up_pity, cr_counter, self.cr_p)
        )

    def _get_dist(
        self, item_num: int, item_pity: int, up_pity: int, cr_counter: int
    ) -> FiniteDist:
        f_dist = self.common_5star(1)
        c_dist = self.common_5star(1, item_pity=item_pity)
        cr_layer = PityLayer(self._get_cr_5star_dist(item_num, up_pity, cr_counter))
        return cr_layer._forward((f_dist, c_dist), 0, 0)

    def __call__(
        self,
        item_num: int = 1,
        multi_dist: bool = False,
        item_pity: int = 0,
        up_pity: int = 0,
        cr_counter: int = 1,
    ) -> Union[FiniteDist, list]:
        if item_num == 0:
            return FiniteDist([1])
        if up_pity and cr_counter == 0:
            raise ValueError("up_pity conflicts with cr_counter == 0")
        if not multi_dist:
            return self._get_dist(item_num, item_pity, up_pity, cr_counter)
        ans_list = [FiniteDist([1])]
        for i in range(1, item_num + 1):
            ans_list.append(self._get_dist(i, item_pity, up_pity, cr_counter))
        return ans_list


class EpitomizedPathModel(GachaModel):
    """Genshin weapon UP model for the 5.0+ Epitomized Path (fate point max 1)."""

    def __init__(self, pity_p1, pity_p2, pity_p3) -> None:
        super().__init__()
        self.base_model = DualPityModel(pity_p1, pity_p2)
        self.up_pity_model = DualPityModel(pity_p1, pity_p3)

    def __call__(
        self,
        item_num: int = 1,
        multi_dist: bool = False,
        item_pity: int = 0,
        ep_pity: int = 0,
        up_pity: int = 0,
    ) -> Union[FiniteDist, list]:
        if (not up_pity) or (ep_pity == 1):
            return self.base_model(item_num, multi_dist, item_pity, ep_pity)
        if item_num == 0:
            return FiniteDist([1])
        if multi_dist:
            return self._get_multi_dist(item_num, item_pity)
        return self._get_dist(item_num, item_pity)

    def _get_multi_dist(self, item_num: int, item_pity: int) -> list:
        first_dist = self.up_pity_model(1, False, item_pity, 0)
        ans_list = [FiniteDist([1]), first_dist]
        if item_num > 1:
            stander_dist = self.base_model(1)
            for i in range(1, item_num + 1):
                ans_list.append(ans_list[i] * stander_dist)
        return ans_list

    def _get_dist(self, item_num: int, item_pity: int) -> FiniteDist:
        first_dist = self.up_pity_model(1, False, item_pity, 0)
        if item_num == 1:
            return first_dist
        return first_dist * self.base_model(item_num - 1)


# Genshin Impact pity tables and shared constants.
PITY_5STAR = np.zeros(91)
PITY_5STAR[1:74] = 0.006
PITY_5STAR[74:90] = np.arange(1, 17) * 0.06 + 0.006
PITY_5STAR[90] = 1

PITY_W5STAR = np.zeros(78)
PITY_W5STAR[1:63] = 0.007
PITY_W5STAR[63:77] = np.arange(1, 15) * 0.07 + 0.007
PITY_W5STAR[77] = 1

# Capturing Radiance trigger probability indexed by counter value (0..3).
CR_P = [0, 0, 0, 1]

# Hard pity bounds (used only for input validation and display).
MAX_CHAR_PITY = len(PITY_5STAR) - 2
MAX_WEAPON_PITY = len(PITY_W5STAR) - 2


class WishCalculator:
    """
    Estimate the chance of reaching a wish goal with a given fate budget.

    Combines the character UP distribution and the weapon UP distribution by
    convolution, then reads the cumulative probability at the available number
    of intertwined fates.
    """

    def __init__(
        self,
        fates: int,
        target_characters: int = 0,
        char_pity: int = 0,
        char_guaranteed: bool = False,
        cr_counter: int = 1,
        target_weapons: int = 0,
        weapon_pity: int = 0,
        weapon_guaranteed: bool = False,
        fate_point: int = 0,
    ) -> None:
        self.fates = fates
        self.target_characters = target_characters
        self.char_pity = char_pity
        self.char_guaranteed = bool(char_guaranteed)
        self.cr_counter = cr_counter
        self.target_weapons = target_weapons
        self.weapon_pity = weapon_pity
        self.weapon_guaranteed = bool(weapon_guaranteed)
        self.fate_point = fate_point
        self._validate()
        self.character_model = CapturingRadianceModel(PITY_5STAR, CR_P)
        self.weapon_model = EpitomizedPathModel(PITY_W5STAR, [0, 0.375, 1], [0, 0.5, 1])

    def _validate(self) -> None:
        checks = [
            (self.fates >= 0, "available fates must be >= 0"),
            (0 <= self.target_characters <= 7, "target characters must be in 0..7"),
            (
                0 <= self.char_pity <= MAX_CHAR_PITY,
                f"character pity must be in 0..{MAX_CHAR_PITY}",
            ),
            (0 <= self.cr_counter <= 3, "capturing radiance counter must be in 0..3"),
            (0 <= self.target_weapons <= 5, "target weapons must be in 0..5"),
            (
                0 <= self.weapon_pity <= MAX_WEAPON_PITY,
                f"weapon pity must be in 0..{MAX_WEAPON_PITY}",
            ),
            (self.fate_point in (0, 1), "fate point must be 0 or 1"),
        ]
        for ok, message in checks:
            if not ok:
                raise ValueError(message)
        if self.char_guaranteed and self.cr_counter == 0:
            self.cr_counter = 1

    def _character_dist(self) -> FiniteDist:
        if self.target_characters == 0:
            return FiniteDist([1])
        return self.character_model(
            self.target_characters,
            item_pity=self.char_pity,
            up_pity=int(self.char_guaranteed),
            cr_counter=self.cr_counter,
        )

    def _weapon_dist(self) -> FiniteDist:
        if self.target_weapons == 0:
            return FiniteDist([1])
        return self.weapon_model(
            self.target_weapons,
            item_pity=self.weapon_pity,
            ep_pity=self.fate_point,
            up_pity=int(self.weapon_guaranteed),
        )

    def compute(self) -> dict:
        """
        Run the model and return a result dictionary.
        ```python
        WishCalculator(fates=180, target_characters=1).compute()

        return = dict  # keys: success_prob, expected, std, quantiles, distribution
        ```
        """
        char_dist = self._character_dist()
        weapon_dist = self._weapon_dist()
        total = char_dist * weapon_dist
        cdf = total.cdf
        if self.fates >= len(cdf):
            success_prob = float(cdf[-1])
        else:
            success_prob = float(cdf[self.fates])
        quantiles = {}
        for q in (0.10, 0.25, 0.50, 0.75, 0.90, 0.99):
            idx = int(np.searchsorted(cdf, q, side="left"))
            quantiles[q] = idx if idx < len(cdf) else None
        return {
            "success_prob": min(success_prob, 1.0),
            "expected": _dist_exp(char_dist) + _dist_exp(weapon_dist),
            "std": (_dist_var(char_dist) + _dist_var(weapon_dist)) ** 0.5,
            "quantiles": quantiles,
            "distribution": total,
        }


def _dist_exp(dist: FiniteDist) -> float:
    """Robust expectation: prefer the model-provided value, fall back to the array."""
    value = float(dist.exp)
    if np.isfinite(value):
        return value
    arr = np.asarray(dist.dist, dtype=float)
    total = arr.sum()
    return calc_expectation(arr / total) if total > 0 else float("nan")


def _dist_var(dist: FiniteDist) -> float:
    """Robust variance: prefer the model-provided value, fall back to the array."""
    value = float(dist.var)
    if np.isfinite(value):
        return value
    arr = np.asarray(dist.dist, dtype=float)
    total = arr.sum()
    return calc_variance(arr / total) if total > 0 else float("nan")


def render_report(config: dict, result: dict) -> str:
    """Build a human-readable, colorized report of the calculation."""
    lines = []
    lines.append(
        CLIStyle.color("=== Genshin Wish Calculator ===", CLIStyle.COLORS["TITLE"])
    )

    lines.append(CLIStyle.color("\nInputs:", CLIStyle.COLORS["SUB_TITLE"]))
    lines.append(
        CLIStyle.color(
            f"  Intertwined fates    : {config['fates']}", CLIStyle.COLORS["CONTENT"]
        )
    )
    lines.append(
        CLIStyle.color(
            f"  Target characters    : {config['target_characters']} "
            f"(pity {config['char_pity']}, guaranteed={config['char_guaranteed']}, "
            f"cr_counter={config['cr_counter']})",
            CLIStyle.COLORS["CONTENT"],
        )
    )
    lines.append(
        CLIStyle.color(
            f"  Target weapons       : {config['target_weapons']} "
            f"(pity {config['weapon_pity']}, guaranteed={config['weapon_guaranteed']}, "
            f"fate_point={config['fate_point']})",
            CLIStyle.COLORS["CONTENT"],
        )
    )

    if config["target_characters"] == 0 and config["target_weapons"] == 0:
        lines.append(
            CLIStyle.color(
                "\nNo target set: choose at least one character or weapon, "
                "or run with --demo to see the default example.",
                CLIStyle.COLORS["WARNING"],
            )
        )
        return "\n".join(lines)

    lines.append(CLIStyle.color("\nDistribution:", CLIStyle.COLORS["SUB_TITLE"]))
    lines.append(
        CLIStyle.color(
            f"  Expected fates needed: {result['expected']:.1f} (std {result['std']:.1f})",
            CLIStyle.COLORS["CONTENT"],
        )
    )

    prob = result["success_prob"]
    prob_color = (
        CLIStyle.COLORS["CONTENT"] if prob >= 0.5 else CLIStyle.COLORS["WARNING"]
    )
    lines.append(CLIStyle.color("\nSuccess probability:", CLIStyle.COLORS["SUB_TITLE"]))
    lines.append(
        CLIStyle.color(f"  With {config['fates']} fates: {prob * 100:.2f}%", prob_color)
    )

    lines.append(
        CLIStyle.color(
            "\nFates needed for confidence level:", CLIStyle.COLORS["SUB_TITLE"]
        )
    )
    for q, value in result["quantiles"].items():
        shown = str(value) if value is not None else "out of range"
        lines.append(
            CLIStyle.color(
                f"  {int(q * 100):>3d}% : {shown}", CLIStyle.COLORS["CONTENT"]
            )
        )

    return "\n".join(lines)


def build_parser() -> ColoredArgumentParser:
    """Create the colorized command-line argument parser."""
    script_name = "wish-calculator.py"
    examples = [
        ("在全新 50/50 下想抽 1 个 UP 角色，有 90 缘", "-c 1 -f 90"),
        (
            "上次歪了（大保底）且已垫 20 抽",
            "-c 1 --char-guaranteed --char-pity 20 -f 70",
        ),
        ("冲角色 1 命（2 个），只看所需抽数表", "-c 2"),
        (
            "1 个角色 + 其专武，已锁定命定值",
            "-c 1 -w 1 --fate-point 1 -f 260",
        ),
        (
            "只抽武器，大保底且已垫 30 抽",
            "-w 1 --weapon-guaranteed --weapon-pity 30 -f 120",
        ),
        ("运行内置默认示例", "--demo"),
    ]
    notes = [
        "1 抽 = 1 个纠缠之缘；用 -f 指定你能投入多少抽。",
        "省略 -f（或填 0）则忽略预算，只看「所需抽数」表。\n",
        "按账号现状对照填写下列参数：",
        "[角色] -c N：想要的 UP 五星份数（N=2 即 1 命，N=7 即 6 命）。",
        "[角色] --char-pity K：距上次角色池出金已垫的抽数，0..89（第 90 抽必出五星）。",
        "[角色] --char-guaranteed：仅当上次五星歪了（非 UP）时才加，此时下个五星必为 UP；处于 50/50 时不要加。",
        "[角色] --cr-counter C：捕获明光计数器 0..3（连续歪后强制必中）；不清楚就保持 1。",
        "------",
        "[武器] -w N：想要的定轨武器份数（N=1 即获得该武器，最多 5 为满精）。",
        "[武器] --weapon-pity K：距上次武器池出金已垫的抽数，0..77（第 80 抽必出五星）。",
        "[武器] --weapon-guaranteed：仅当上次武器五星歪了（非两把 UP 之一）时才加。",
        "[武器] --fate-point：已锁定所选武器（命定值为 1）填 1，否则填 0。\n",
        "所有可选参数默认对应全新卡池：垫抽 0、无大保底、命定值 0、明光计数器 1。",
        "最终输出：用 -f 缘达成目标的概率、期望所需抽数、各置信度所需抽数。",
        "--demo：忽略其它所有参数，运行内置默认示例。",
    ]
    parser = ColoredArgumentParser(
        description="原神抽卡计算器，估算在给定纠缠之缘预算下达成抽卡目标的概率 (based on `https://github.com/OneBST/GGanalysis.git`）",
        epilog=create_example_text(script_name, examples, notes),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-f", "--fates", type=int, default=0, help="可用的纠缠之缘数量")
    parser.add_argument(
        "-c",
        "--target-characters",
        type=int,
        default=0,
        help="想要的 UP 五星角色个数（0..7）",
    )
    parser.add_argument(
        "--char-pity", type=int, default=0, help="角色池已垫抽数（0..89）"
    )
    parser.add_argument(
        "--char-guaranteed",
        action="store_true",
        help="角色池处于大保底（下个五星必为 UP）",
    )
    parser.add_argument(
        "--cr-counter", type=int, default=1, help="捕获明光计数器（0..3）"
    )
    parser.add_argument(
        "-w",
        "--target-weapons",
        type=int,
        default=0,
        help="想要的定轨 UP 五星武器个数（0..5）",
    )
    parser.add_argument(
        "--weapon-pity", type=int, default=0, help="武器池已垫抽数（0..77）"
    )
    parser.add_argument(
        "--weapon-guaranteed",
        action="store_true",
        help="武器池处于大保底（下个五星必为 UP）",
    )
    parser.add_argument(
        "--fate-point", type=int, default=0, help="定轨命定值（0 或 1）"
    )
    parser.add_argument("--demo", action="store_true", help="运行内置的默认示例")
    parser.add_argument("--log", action="store_true", help="开启调试模式")
    return parser


def main() -> int:
    """Main program logic."""
    global DEBUG_MODE
    parser = build_parser()
    args = parser.parse_args()
    DEBUG_MODE = args.log

    if args.demo:
        config = dict(DEFAULT_DEMO_CONFIG)
        print(
            CLIStyle.color(
                "Demo mode: running the built-in default example.",
                CLIStyle.COLORS["WARNING"],
            )
        )
    else:
        config = {
            "fates": args.fates,
            "target_characters": args.target_characters,
            "char_pity": args.char_pity,
            "char_guaranteed": args.char_guaranteed,
            "cr_counter": args.cr_counter,
            "target_weapons": args.target_weapons,
            "weapon_pity": args.weapon_pity,
            "weapon_guaranteed": args.weapon_guaranteed,
            "fate_point": args.fate_point,
        }

    try:
        calculator = WishCalculator(**config)
        result = calculator.compute()
    except ValueError as e:
        print(CLIStyle.color(f"Error: {str(e)}", CLIStyle.COLORS["ERROR"]))
        return 1
    except Exception as e:
        if DEBUG_MODE:
            import traceback

            traceback.print_exc()
        print(CLIStyle.color(f"Error: {str(e)}", CLIStyle.COLORS["ERROR"]))
        return 1

    print(render_report(config, result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
