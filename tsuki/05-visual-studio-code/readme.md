kali 默认自带 code-oss，如果卸载掉 code-oss，会导致潜在的依赖不完整问题，特地弄一个 vscode.appimage 解决

1. vscode official repo：https://github.com/microsoft/vscode.git
2. build method refers to：https://github.com/valicm/VSCode-AppImage.git
3. build tool：https://github.com/valicm/appimage-bash/blob/main/build.sh

## usage

1. linux

	```bash
	chmod +x ./build.sh
	./build.sh build
	
	dist/vscode-xxxxx-x86_64.AppImage --appimage-extract
	```

	如果想查看 appimage 解压运行时，通过 `dist/vscode-xxxxx-x86_64.AppImage --appimage-mount` 可以进入到 fuse 挂载类型的目录查看

2. docker

	```bash
	docker-compose -f build.yml up --build
	
	dist/vscode-xxxxx-x86_64.AppImage --appimage-extract
	```

## fetch config

1. ``