Feature: EA Request 自动化验收测试 (UAT)
  As a normal user
  I want to create an EA Request by selecting projects and uploading diagrams
  So that the technical review process can be initiated

  Background: 初始状态
    Given 用户打开 EA Portal "http://localhost:3000"

  Scenario: 完整创建 EA Request 流程（包含 ADFS 状态检测与双图上传）
    # 第一步：登录检测 (ADFS SSO)
    When 检查页面右上角是否显示 "Log Out" 按钮
    Then 如果未发现 "Log out"，则判定为未登录状态并挂起等待用户完成 ADFS 认证
    And 确认登录成功后，用户应停留在 主页面

    # 第二步：项目初始化
    When 用户点击主页面的 "Create A Request" 按钮
    And 用户在项目列表执行以下操作之一:
      | Action        | Details                               |
      | 选择现有项目   | 从下拉列表中匹配 "sample.json" 中的 Project ID |
      | 创建新项目     | 输入新项目名称及描述信息                   |

    # 第三步：架构图上传
    And 依次上传所需的架构图文件:
      | 类别          | 本地文件路径                               | 逻辑参考       |
      | 应用架构图    | test-data/ea-request/app-diagram/app.png   | app-diagram    |
      | 技术架构图    | test-data/ea-request/tech-diagram/tech.png | tech-diagram   |
    
    # 第四步：确认与提交
    And 用户检查表单预览，确认信息无误后点击 "Confirm to Submit"
    Then 页面应跳转至成功反馈页并显示 "This request is in queue, please wait for the EA team to process it."
    And 记录页面上显示的 "Request ID" 或是时间戳以供后续 UAT 审计