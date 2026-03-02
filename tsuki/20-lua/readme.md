
## unluac

https://github.com/HansWessels/unluac.git

```bash
cd src
mkdir build
javac -verbose -deprecation -Werror -d build unluac/*.java
jar cfe ./unluac.jar unluac.Main -C build .
```

## luadec

https://github.com/viruscamp/luadec.git

```bash
VERSION=5.1

git clone https://github.com/viruscamp/luadec
cd luadec
git submodule update --init lua-$VERSION
cd lua-$VERSION
make linux
cd ../luadec
make LUAVER=$VERSION
```