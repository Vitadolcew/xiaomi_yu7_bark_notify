一个可以自动获取小米 YU7 交付进度，通过 Bark 通知给用户的脚本。

> 支持 Github Action / 青龙面板 / Node-RED 设置定时查询

> 根据预计交付周数转换为预计提车日期

> 集成延保服务状态/vid状态提示


![img](/img/para_succeed.jpg)

> 本脚本采用 Cookie 的方式进行获取数据，可能存在 Cookie 过期的情况，需要手动更新

> 青龙面板的定时可能更准确一些

## Github Action

如果你想通过 Github Action 来实现定时获取数据，可进行以下步骤

1. fork 本项目到你自己的仓库，然后修改 fork 仓库内的 `.github/workflows/run_notify_sync.yml`文件，以下内容改为你自己的 github 信息（可选）。
   

```bash
# 默认执行时间是每5分钟会自动执行脚本。

# 如需修改时间，可修改以下代码的`cron`
on:
  workflow_dispatch:
  schedule:
    - cron: '*/5 * * * *'
```

2. 为 GitHub Actions 添加代码提交权限 访问 repo Settings > Actions > General 页面，找到 Workflow permissions 的设置项，将选项配置为 Read and write permissions。

   > 如果不设置允许的话，会导致 workflows 无法更新配置文件

3. 在 repo Settings > Security > Secrets > secrets and variables > Actions > New repository secret > 增加:

   `ORDERID`、`USERID`、`COOKIE`、`CARSHOPCOOKIE`、`DEVICE_TOKEN` 这 5 个变量

   ![img](/img/添加变量.png)

4. `ORDERID`、`USERID`、`COOKIE` 获取方法：

   使用[Reqable](https://reqable.com/zh-CN)等抓包工具，抓取`小米汽车微信小程序`

   查看：`https://api.retail.xiaomiev.com/mtop/car-order/order/detail`

- `ORDERID`、`USERID` 的获取：

  ![img](/img/1.png)

- `COOKIE` 的获取

> 注意：COOKIE 变量在粘贴到 github action 时，首尾要添加`"`符号

![img](/img/2.png)

5. CARSHOPCOOKIE 获取方法：

   使用[Reqable](https://reqable.com/zh-CN)等抓包工具，抓取`小米汽车App`

   查看：`https://carshop-api.retail.xiaomiev.com/mtop/carlife/product/info`

   搜索“延保”，查询“原始”的 Cookie

   ![img](/img/4.png)

6. DEVICE_TOKEN 的获取
   IOS 下载`Bark`-->服务器-->复制 device_token
   ![img](/img/3.png)

> 在 device_token 正确的情况下，运行 action 后，如果 ORDERID、USERID、COOKIE 任意一个参数存在问题，会发送错误提醒

![img](/img/para_error.jpg)

## 青龙面板

如果你是和我一样，是一个略懂青龙面板的“脚本小子”，也可以通过以下来设置定时任务来执行脚本

1. 安装 Python 依赖：requests、toml
   ![img](/img/ql-1.png)

2. 复制文件

- 需复制文件：yu7_notify.py、configBAK.toml（需手动改名为 config.toml）

- 修改 config.toml 当中的 orderId、userId、Cookie、device_token（取值来源可参考上文）
  ![img](/img/ql-2.1.png)
  ![img](/img/ql-2.2.png)

> 如果是 docker 部署的青龙面板，可以将上述 2 个文件复制粘贴到宿主机对应的目录

3. 调试脚本（可选）
   ![img](/img/ql-3.1.png)

   ![img](/img/ql-3.2.png)

> 如果依赖安装正常、账号参数正确，则会输出对应的日志提示

4. 设置定时任务

- 名称：`yu7_notify`（可修改）

- 命令/脚本：`python  /ql/data/scripts/yu7_notify/yu7_notify.py`

- 定时规则：`*/5 * * * *` (默认每 5 分钟执行一次)

![img](/img/ql-4.1.png)

![img](/img/ql-4.2.png)

## Node-RED + home-assistant

如果你恰好是一个智能家居爱好者，可以通过 Node-RED 来获取信息，并在 home-assitant 当中展示

1. 前置步骤：

- 你的 ha 和 NR 已经完成连接

- 已在 NR 当中安装`Node-RED-contrib-http-request`这个节点

- 已将对应的 HA server 更换为你自己的配置

2. NR 导入文件`yu7_notify.json`

3. 复制文件

- 需复制`Node-RED`下的 2 个文件：config.json、yu7_notify.json

- 修改 config.json 当中的 orderId、userId、Cookie、device_token（取值来源可参考上文）

![img](/img/nr-3.png)

> 如果是 docker 部署的 Node-RED，可以将上述 2 个文件复制粘贴到宿主机对应的目录

4. 修改执行周期

默认是每 5 分钟执行一次，可手动修改】

![img](/img/nr-4.png)

5. HA 实体

当运行成功一次后，会在 HA 当中新增实体，之后可以尽情发挥你的想象力了！

![img](/img/nr-5.png)
