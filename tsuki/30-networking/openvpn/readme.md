# OpenVPN

预留给 OpenVPN 的探索与实现，目前尚无配置或已验证的部署。

共享文档放在 [docs/](../docs/)，公开配置参考放在 [configs/](../configs/)。其中现有配置属于 WireGuard，不能直接用作 OpenVPN 配置。

## 私有 handoff 与 agent 接管

本协议的真实环境、管理入口、验证证据和下一步操作记录放在本目录的 `handoff/`，整个目录被 Git 忽略。后续建立档案时写明当前状态、授权范围、最后验证时间、执行位置和完成判据；agent 先核对这些信息再操作。

密码、私钥和 token 只引用安全存储位置。handoff 应为 owner-only 并单独备份；公开克隆后可在本目录执行 `mkdir -p -m 700 handoff` 创建。
