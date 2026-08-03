# init

1.   zsh：`curl -fLo ~/.zshrc https://raw.githubusercontent.com/sparkuru/genshin/main/mtf/.zshrc`

2.   powershell：`curl -fLo $PROFILE https://raw.githubusercontent.com/sparkuru/genshin/main/mtf/powershell_profile.ps1`

3.   ssh：

     ```bash
     GITHUB_ENDPOINT="https://raw.githubusercontent.com/sparkuru/genshin/main"
     mkdir -p ~/.ssh && curl -fLo ~/.ssh/authorized_keys $GITHUB_ENDPOINT/mtf/authorized_keys && chmod 700 -R $HOME/.ssh
     sudo curl -fLo /etc/ssh/sshd_config $GITHUB_ENDPOINT/mtf/etc/sshd_config
     systemctl start ssh && systemctl enable ssh
     ```

4.   vim

     ```bash
     GITHUB_ENDPOINT="https://raw.githubusercontent.com/sparkuru/genshin/main"
     sudo apt-get install -y vim fzf ripgrep
     curl -fLo /tmp/unix-install-vim.sh $GITHUB_ENDPOINT/mtf/unix-install-vim.sh && chmod +x /tmp/unix-install-vim.sh && sudo /tmp/unix-install-vim.sh install
     ```

5.   unix environment

     ```bash
     GITHUB_ENDPOINT="https://raw.githubusercontent.com/sparkuru/genshin/main"
     sudo curl -fLo /etc/environment $GITHUB_ENDPOINT/mtf/etc/environment
     sudo curl -fLo /etc/dhcpcd.conf $GITHUB_ENDPOINT/mtf/etc/dhcpcd.conf
     ```

7.   KDE Plasma 6

     ```bash
     GITHUB_ENDPOINT="https://raw.githubusercontent.com/sparkuru/genshin/main"
     mkdir -p "$HOME/.local/share/kde-deploy"
     curl -fsSLo "$HOME/.local/share/kde-deploy/kde-config.sh" $GITHUB_ENDPOINT/mtf/kde/kde-config.sh
     bash "$HOME/.local/share/kde-deploy/kde-config.sh" deploy
     ```

     此配置包仅管理通用外观与单击行为；不会收集文件路径、最近记录、快捷键、屏幕布局、会话或窗口状态。

     备份当前 KDE 配置到本仓库：

     ```bash
     ./kde/kde-config.sh backup
     git add kde && git commit -m 'backup KDE configuration'
     ```
