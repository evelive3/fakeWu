-- 机构基础视图
CREATE VIEW [dbo].[app_branch_view] AS
SELECT
	uv.staff_branch_id,
	uv.branch_name,
	uv.groups,
	uv.group_name,
	SUM (uv.prem) AS prem,
	SUM (uv.finished) AS finished,
	SUM (uv.sell_target) AS target
FROM
	app_user_view AS uv
GROUP BY
	uv.staff_branch_id,
	uv.branch_name,
	uv.groups,
	uv.group_name
GO

-- 日志基础视图
CREATE VIEW [dbo].[app_log_view] AS
SELECT
	l.id as log_id,
	u.id AS staff_id,
	u.staff_name,
	l.cust_name,
	u.sell_target,
	b.id AS branch_id,
	b.branch_name,
	b.groups AS group_id,
	b.group_name,
	l.op_at,
	l.op_user_id,
	(select u2.staff_name from app_user as u2 where l.op_user_id=u2.id) as op_user_name,
	COUNT (l.staff_id) AS finished,
	SUM (l.prem) AS prem
FROM
	app_log AS l,
	app_branch AS b,
	app_user AS u
WHERE
	l.staff_id = u.id
AND l.branch_id = b.id
GROUP BY
	l.id,
	u.id,
	u.staff_name,
	l.cust_name,
	u.sell_target,
	b.id,
	b.branch_name,
	b.groups,
	b.group_name,
	l.op_at,
	l.op_user_id
GO

-- 用户基础视图
CREATE VIEW [dbo].[app_user_view] AS
SELECT
	u.id AS staff_id,
	u.staff_no,
	u.staff_name,
	u.sell_target,
	(
		SELECT
			COUNT (l.staff_id)
		FROM
			app_log AS l
		WHERE
			l.staff_id = u.id
	) AS finished,
	(
		SELECT
			ISNULL(SUM (l.prem), 0)
		FROM
			app_log AS l
		WHERE
			l.staff_id = u.id
	) AS prem,
	b.id AS staff_branch_id,
	b.branch_name,
	b.groups,
	b.group_name
FROM
	app_branch AS b,
	app_user AS u
WHERE
	u.branch_id = b.id
AND u.sell_target != 0
GO

-- 公司每日视图
CREATE VIEW [dbo].[day_company_view] AS
SELECT
	al.group_id,
	al.group_name,
	SUM (al.prem) AS prem,
	SUM (al.finished) AS finished,
	al.op_at
FROM
	app_log_view AS al
GROUP BY
	al.group_id,
	al.group_name,
	al.op_at
GO

-- 机关每日视图
CREATE VIEW [dbo].[day_dept_view] AS
SELECT
	al.branch_id,
	al.branch_name,
	SUM (al.prem) AS prem,
	SUM (al.finished) AS finished,
	al.op_at
FROM
	app_log_view AS al
where
	al.group_id=1
GROUP BY
	al.branch_id,
	al.branch_name,
	al.op_at
GO

-- 个人每日视图
CREATE VIEW [dbo].[day_person_view] AS
SELECT
	al.staff_name,
	al.branch_name,
	SUM (al.prem) AS prem,
	SUM (al.finished) AS finished,
	al.op_at,
	al.op_user_id,
	al.op_user_name
FROM
	app_log_view AS al
GROUP BY
	al.staff_name,
	al.branch_name,
	al.op_at,
	al.op_user_id,
	al.op_user_name
GO

-- 公司汇总视图
CREATE VIEW [dbo].[total_company_view] AS
SELECT
	rank () OVER (

		ORDER BY
			(
				SUM (finished) * 1.0 / SUM (target) * 1.0
			) DESC
	) AS pm,
	groups as group_id,
	group_name,
	SUM (prem) AS prem,
	SUM (finished) AS finished,
	SUM (target) AS target
FROM
	app_branch_view
GROUP BY
	groups,
	group_name
GO

-- 机关汇总视图
CREATE VIEW [dbo].[total_dept_view] AS
SELECT
	rank () OVER (

		ORDER BY
			(
				SUM (finished) * 1.0 / SUM (target) * 1.0
			) DESC
	) AS pm,
	app_branch_view.staff_branch_id as branch_id,
	app_branch_view.branch_name,
	SUM (prem) AS prem,
	SUM (finished) AS finished,
	SUM (target) AS target
FROM
	app_branch_view
WHERE
	app_branch_view.groups = 1
GROUP BY
	app_branch_view.staff_branch_id,
	app_branch_view.branch_name
GO

-- 个人汇总视图
CREATE VIEW [dbo].[total_person_view] AS
SELECT top 8
	uv.staff_id,
	uv.staff_name,
	uv.branch_name,
	uv.finished,
	uv.prem
FROM
	app_user_view AS uv
ORDER BY prem desc, finished desc
GO