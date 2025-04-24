# 大模型API测速工具配置指南

## 配置文件说明

配置文件使用YAML格式，默认路径为`config.yaml`。主要包含以下部分：
```yaml
providers:
  - name: "服务商名称"  # 必须唯一
    base_url: "API基础地址"
    api_key: "API密钥"
    models:
      - name: "模型名称"
        params:
          temperature: 0.7  # 采样温度
          max_tokens: 1000  # 最大token数

test_prompt: "请用中文回答：大语言模型API性能测试的关键指标有哪些？"
```

### 1. providers 配置

```yaml
providers:
  - name: "服务商名称"  # 必须唯一
    base_url: "API基础地址"
    api_key: "API密钥"
    models:
      - name: "模型名称"
        params:
          temperature: 0.7  # 采样温度
          max_tokens: 1000  # 最大token数
```

- 每个provider代表一个API服务商
- `name`字段必须唯一，不能重复
- `base_url`为API端点地址
- `api_key`为对应服务商的认证密钥
- `models`下可配置多个模型及其参数

### 2. 测试提示语配置

```yaml 
test_prompt: "请用中文回答：大语言模型API性能测试的关键指标有哪些？"
```

- 这是用于测试的标准提示语
- 建议使用中文以避免tokenizer差异

### 3. 配置示例

项目提供YAML格式的配置文件示例：
- 模板文件: `template/config.yaml`

建议复制模板文件到项目根目录后修改使用。

## 注意事项

1. 请妥善保管API密钥
2. provider名称不能重复
3. 参数值应符合各API服务商的要求
4. 修改配置后需要重启测试工具