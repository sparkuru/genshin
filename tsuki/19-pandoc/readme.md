
pandoc: https://github.com/jgm/pandoc.git

## installation

`sudo apt install pandoc`

## usage

1. convert markdown to docx: `pandoc --from/-f markdown --to/-t docx --reference-doc </path/to/custom-reference.docx> </path/to/src/file.md> --output/-o </path/to/output.docx>`

2. use pandoc convert markdown to docx, then pass through `python-docx` to apply custom table and caption styles: `uv add python-docx`

script: `./pandoc-md2docx.sh` does the above two steps.

## wps view option

### 页面显示选项

- [x] 任务窗格(R)
- [ ] 隐藏空白(B)
- [x] 垂直标尺(C)
- [x] 状态栏(U)
- [x] 进入页眉页脚提示(Q)
- [x] 选择时显示浮动工具栏(D)
- [x] 右键时显示浮动工具栏(G)
- [x] 屏幕提示(N)
- [x] 启用实时预览(V)
- [x] 经典菜单按钮(Z)
- 导航窗格(P)：靠左

### 显示文档内容

- [x] 突出显示(H)
- [x] 正文边框(X)
- [x] 裁剪标记(R)
- [ ] 域代码(F)
- [ ] 书签(K)
- 域底纹(E)：选取时显示

### 格式标记

- [x] 空格(S)
- [ ] 段落标记(M)
- [ ] 对象位置(J)
- [x] 制表符(I)
- [ ] 隐藏文字(I)
- [ ] 全部(L)

### 功能区选项

- [ ] 双击选项卡时隐藏功能区(A)
- [ ] 单击方框时打勾(O)
- [ ] 打开文件，展示智能识别目录(W)
- [x] 用 Ctrl + 单击跟踪超链接(O)