import requests
import json
import os
from datetime import datetime
import toml
import os
import sys
import re
import argparse
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.WARNING, format="%(message)s")  # 设置日志级别
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
BIN = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(BIN, "config.toml")
badge_week = None


def load_config():
    config = toml.load(config_path)

    if args.cookie:
        print("使用命令行参数传入账号参数...")
        return (
            args.orderId,
            args.userId,
            args.cookie,
            args.carshopCookie if args.carshopCookie else None,
            args.device_token,
            config["notice"]["deliveryTimeLatest"],
            config["notice"]["carshopNotice"],
            config["notice"]["remarks"],
            config["notice"]["errorTimes"],
        )

    try:
        print("使用config.toml传入账号参数...")
        return (
            config["account"]["orderId"],
            config["account"]["userId"],
            config["account"]["Cookie"],
            (
                config["account"]["carshopCookie"]
                if config["account"]["carshopCookie"]
                else None
            ),
            config["account"]["deviceToken"],
            config["notice"]["deliveryTimeLatest"],
            config["notice"]["carshopNotice"],
            config["notice"]["remarks"],
            config["notice"]["errorTimes"],
        )
    except:
        print("请检查config.toml文件的参数是否完整/正确！")
        sys.exit()


def calculate_delivery_date(delivery_time, lock_time):
    # 提取周数信息
    weeks_pattern = r"(\d+)-(\d+)周"
    weeks_matches = re.findall(weeks_pattern, delivery_time)

    if not weeks_matches:
        return ""

    min_weeks = int(weeks_matches[-1][0])
    max_weeks = int(weeks_matches[-1][1])

    global badge_week
    badge_week = min_weeks
    # 默认使用第2个周数范围的结果和当前日期做比较
    current_date = datetime.now()
    # 如果只存在1个周数范围结果，则使用第1个周数范围的结果和锁单日期做比较
    if len(weeks_matches) == 1:
        current_date = datetime.strptime(lock_time, "%Y-%m-%d %H:%M:%S")

    # 计算交付日期范围
    delivery_start_date = current_date + timedelta(weeks=min_weeks)
    delivery_end_date = current_date + timedelta(weeks=max_weeks)
    delivery_date_range = f"⏳ 预计提车日期：{delivery_start_date.strftime('%Y-%m-%d')} 至 {delivery_end_date.strftime('%Y-%m-%d')}"

    return delivery_date_range


def get_order_detail(orderId, userId, Cookie):
    url = "https://api.retail.xiaomiev.com/mtop/car-order/order/detail"

    payload = [{"orderId": orderId, "userId": userId}]

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.60(0x18003c31) NetType/4G Language/zh_CN",
        "Accept-Encoding": "gzip,compress,br,deflate",
        "Content-Type": "application/json",
        "configSelectorVersion": "2",
        "content-type": "application/json; charset=utf-8",
        "deviceappversion": "1.16.0",
        "x-user-agent": "channel/car platform/car.wxlite",
        "Referer": "https://servicewechat.com/wx183d85f5e5e273c6/93/page-frame.html",
        "Cookie": Cookie,
    }

    response = requests.post(url, data=json.dumps(payload), headers=headers)

    data = response.json().get("data", {})
    logo_link = data.get("backdropPictures", {}).get("backdropPicture", None)
    statusInfo = data.get("statusInfo", {})
    vid = data.get("buyCarInfo", {}).get("vid", "")
    orderTimeInfo = data.get("orderTimeInfo", {})

    order_status_name = statusInfo.get("orderStatusName", None)
    order_status = statusInfo.get("orderStatus")
    delivery_time = orderTimeInfo.get("deliveryTime")

    vid_text = f"🛠️ vid：{vid}【{vid_status_mapping(str(vid))}】"
    remarks_text = " " * 50 + remarks

    if not delivery_time:
        delivery_time = "请检查account参数是否正确！"
        error_times_update = error_times + 1

        message = f"{delivery_time}\n\n失败次数：{error_times_update}\norderId：{orderId}\nuserId：{userId}\nCookie：{Cookie}\n【失败次数超过3次后将停止发送】\n\n{remarks_text}\n\n{order_status}"

        save_config(
            delivery_time,
            order_status,
            carshop_notice=carshop_notice,
            error_times=error_times_update,
        )
        if error_times_update <= 3:
            send_bark_message(device_token, message, orderStatusName="account参数错误")

        logger.warning(delivery_time)
        sys.exit()
    add_time = orderTimeInfo.get("addTime")
    pay_time = orderTimeInfo.get("payTime")
    lock_time = orderTimeInfo.get("lockTime")
    goods_names = " | ".join(
        item.get("goodsName", "") for item in data.get("orderItem", [])
    )
    delivery_date_range = calculate_delivery_date(delivery_time, lock_time)
    text = f"{delivery_date_range}\n\n📅 下定时间：{add_time}\n💳 支付时间：{pay_time}\n🔒 锁单时间：{lock_time}\n\n🛍️ 配置：{goods_names}\n\n{vid_text}\n\n{remarks_text}"
    # print(text)

    return delivery_time, order_status, text, order_status_name, logo_link, vid


def vid_status_mapping(vid):
    if vid.startswith("HXM"):
        text = "已下线"
    else:
        text = "未下线"
    return text


def get_carshop_info(Cookie):
    if not Cookie:
        return None

    url = "https://carshop-api.retail.xiaomiev.com/mtop/carlife/product/info"

    payload = [{}, {"productId": "21430", "servicePackageVersion": 2}]

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MIOTStore/20191212 (micar;1.16.2;f37b2fb7-33c7-4295-9d4b-a5d29881b7f5;NaNI;00000000-0000-0000-0000-000000000000;)",
        "Content-Type": "application/json",
        "referer": "https://carshop-api.retail.xiaomiev.com",
        "x-mishop-app-source": "front-RN",
        "x-user-agent": "channel/car platform/carlife.ios",
        "mishop-model": "iPhone15,3",
        "accept-language": "zh-CN,zh-Hans;q=0.9",
        "Cookie": Cookie,
    }

    response = requests.post(url, data=json.dumps(payload), headers=headers)
    notice = response.json().get("data", {}).get("product", {}).get("notice", None)
    if not notice:
        return None, None
    if notice in ["账号内暂无绑定车辆，请绑定后再来购买", "暂不符合购买条件"]:
        notice_text = notice + "【状态无更新】"
    else:
        notice_text = notice + "【状态有更新，可以问问交付专员！】"
    if not notice:
        logger.warning("已检测到存在carshopCookie，但是无法获取数据")
    return notice, notice_text


def save_config(delivery_time, order_status, carshop_notice=None, error_times=0):
    # 先加载当前的配置
    config = toml.load(config_path)

    if args.cookie:
        account = {
            "orderId": "",
            "userId": "",
            "Cookie": "",
            "carshopCookie": "",
            "deviceToken": "",
        }
        config["account"] = account

    # 更新 deliveryTimeLatest 和 carshopNotice
    notice = {
        "deliveryTimeLatest": delivery_time,
        "carshopNotice": carshop_notice if carshop_notice else "",
        "remarks": config["notice"]["remarks"],
        "errorTimes": error_times,
        "orderStatus": order_status,
    }
    config["notice"] = notice

    # 写入更新后的配置到文件
    with open(config_path, "w", encoding="utf-8") as f:
        toml.dump(config, f)


def send_bark_message(token, message, logo_link=None, order_status_name=None):

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    icon_link = "https://upload.wikimedia.org/wikipedia/commons/4/4f/Xiaomi_EV_New.jpg"
    if logo_link:
        icon_link = logo_link
    if order_status_name:
        title = f"【小米汽车】{order_status_name}({current_time})"
    else:
        title = f"【小米汽车】进度查询({current_time})"

    url = f"https://api.day.app/{token}"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
    }

    data = {
        "body": message,
        "group": "小米汽车通知",
        "title": title,
        "subtitle": f"📦 交付进度：{delivery_time}",
        "icon": icon_link,
        "isArchive": 1,
    }
    if badge_week:
        data["badge"] = badge_week

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return True
    else:
        print("请检查Bark的token是否正确！")
        sys.exit()


def main():
    if vid.startswith("HXM"):
        if send_bark_message(device_token, message, logo_link, order_status_name):
            print("vid状态已更新，消息已发送成功！")
        else:
            print("vid状态已更新，消息发送失败。")
        sys.exit()

    if (delivery_time != old_delivery_time) or (carshop_notice != old_carshop_notice):
        save_config(
            delivery_time, order_status, carshop_notice=carshop_notice
        )  # 更新配置文件
        if send_bark_message(device_token, message, logo_link, order_status_name):
            print("消息已发送成功！")
        else:
            print("消息发送失败。")
    else:
        print("交付时间/vid没有更新。")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load configuration from command line."
    )
    parser.add_argument("--orderId", type=str, help="Order ID")
    parser.add_argument("--userId", type=str, help="User ID")
    parser.add_argument("--cookie", type=str, help="User Cookie")
    parser.add_argument("--carshopCookie", type=str, help="User cargo cookie")
    parser.add_argument(
        "--device_token",
        type=str,
        help="Device Token",
    )
    args = parser.parse_args()
    # print(args)
    (
        orderId,
        userId,
        Cookie,
        carshop_cookie,
        device_token,
        old_delivery_time,
        old_carshop_notice,
        remarks,
        error_times,
    ) = load_config()
    carshop_notice, carshop_notice_text = get_carshop_info(carshop_cookie)
    delivery_time, order_status, message, order_status_name, logo_link, vid = (
        get_order_detail(orderId, userId, Cookie)
    )

    main()
