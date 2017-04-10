-- 机构表
CREATE TABLE [dbo].[app_branch] (
[id] int IDENTITY(1,1) PRIMARY KEY,
[branch_name] varchar(30) NULL ,  -- 机构名称
[groups] int NULL ,  -- 机构分组
[group_name]  varchar(30) NULL  -- 分组名称
);

-- 用户表
CREATE TABLE [dbo].[app_user] (
[id] int IDENTITY(1,1) PRIMARY KEY ,
[staff_no] varchar(30) NULL ,  -- 员工工号
[staff_name] varchar(30) NULL ,  -- 员工姓名
[branch_id] int FOREIGN KEY REFERENCES app_branch(id) ,  -- 所属机构id
[wx_remark] varchar(40) UNIQUE ,  -- 微信备注名
[sell_target] int NULL ,  -- 销售目标
[is_auth] bit DEFAULT 0 ,  -- 能否使用系统功能
[is_superuser] bit DEFAULT 0  -- 是否管理员
);

-- 日志表
CREATE TABLE [dbo].[app_log] (
[id] int IDENTITY(1,1) PRIMARY KEY ,
[staff_id] int FOREIGN KEY REFERENCES app_user(id) ,  -- 员工id
[cust_name] varchar(30) NULL ,  -- 客户姓名
[car_no] varchar(30) NULL ,  -- 客户车牌号
[cust_phone] varchar(30) NULL ,  -- 客户电话
[cust_id] varchar(30) NULL ,  -- 客户身份证
[clerk_id] varchar(20) NULL ,  -- 挂靠销售员工号
[op_at] date NULL ,  -- 操作日期
[prem] int NULL ,  -- 保费
[branch_id]  int FOREIGN KEY REFERENCES app_branch(id) ,  -- 机构id
[op_user_id] int FOREIGN KEY REFERENCES app_user(id)  -- 操作员id
);

