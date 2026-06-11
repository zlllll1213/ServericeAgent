const prompts = [
  ["查订单 10001", "帮我查一下订单 10001 到哪里了"],
  ["我要退货", "我要退货"],
  ["10001", "10001"],
  ["买错了", "买错了"],
  ["确认", "确认"],
  ["取消", "取消"],
  ["连接 WiFi", "路由器怎么连接 WiFi"],
  ["7 天退货规则", "7 天无理由退货规则是什么"],
  ["macOS 支持", "SmartRouter X1 支持 macOS 吗"],
  ["投诉转人工", "我要投诉，转人工客服"],
  ["转人工客服", "我要找人工客服"],
];

export const promptPanel = {
  init(container, onSelect) {
    container.innerHTML = "";
    for (const [label, value] of prompts) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = label;
      button.addEventListener("click", () => onSelect(value));
      container.append(button);
    }
  },
};
