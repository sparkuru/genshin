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
     ./sync-kde.sh -u USERNAME --host HOST    # preview the change
     ./sync-kde.sh --apply -u USERNAME --host HOST # confirm sync
     ```