# Yiyan-Cli
Yiyan Command Client 

```
python yiyan.py --prompt=yes
```

注意需要将名为 Default 的 UserDirectory 放入到当前目录下，并配置 UserDirectory。

也可以通过切换为 login 来登录。

## Installation

0. 安装 Python3.8，同时安装 xkvim 的依赖。

1. 安装 Chrome 依赖

```
~/xkvim/install_sh/install_chrome.sh
```

3. 跟新Chrome的版本，具体版本在 yiyan.py，修改库中的版本号。

3. 设置 Cookies 

运行 http_proxy.py 来设置代理
运行 python yiyan.py --debug=yes 来获取chrome的执行指令

然后 使用远程调试来进行登录。成功登录后会记录cookies

4. 运行下面指令，并通过报错调试最新的Web版本。

```
python yiyan.py --prompt=yes
```
成功输出yiyan回复就可以进行下一步了。

5. 运行即可。