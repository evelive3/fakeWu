import itchat
from arrow import Arrow
from datetime import timedelta
import re
import pyodbc

# ----------SETTING------------
fields = ['员工', '车主', '车牌', '车主电话', '身份证', '销售员工号', '保费']
wc_single_line_max = 50  # 微信半角字符单行最大长度
sep = f'{"-"*wc_single_line_max}\n'
single_day = timedelta(1)
# ----------SETTING------------
conn = pyodbc.connect(r'DRIVER={SQL Server};SERVER=10.150.192.10;DATABASE=jcx;UID=sa;PWD=Yaclic1234')
cursor = conn.cursor()


def refind(pa, st):
    """
    返回正则查找结果
    :param pa: 
    :param st: 
    :return: 
    """
    result = re.findall(pa, st)
    if result:
        return result[0]
    return None


def get_userinfo(staff_name):
    """
    根据员工姓名获取员工信息
    :param staff_name: 
    :return: 
    """
    cursor.execute(
        'SELECT u.id, u.staff_name, u.branch_id, b.branch_name, b.groups, b.group_name from app_user as u, app_branch as b where u.branch_id=b.id and u.staff_name=?',
        (staff_name,))
    result = cursor.fetchone()
    if result:
        staff_id, staff_name, branch_id, branch_name, group_id, group_name = result
        return staff_id, staff_name, branch_id, branch_name, group_id, group_name
    return None


def is_authuser(wx_remark):
    """
    根据输入微信备注名，读取用户表内容并返回该用户是否为授权用户
    
    :param wx_remark: 微信备注名
    :return: 如果微信备注名为空，或不在用户表内，或不在授权用户列表，返回False
    staff_id, staff_name, branch_id
    """
    if not wx_remark:
        return False
    cursor.execute(
        'SELECT u.id, u.staff_name, u.branch_id, b.branch_name, b.groups, b.group_name from app_user as u, app_branch as b where u.branch_id=b.id and u.wx_remark=? and u.is_auth=1',
        (wx_remark,))
    result = cursor.fetchone()
    if result:
        staff_id, staff_name, branch_id, branch_name, group_id, group_name = result
        return staff_id, staff_name, branch_id, branch_name, group_id, group_name
    return False


def is_superuser(fromusername, tousername, wx_remark):
    """
    根据微信备注名获取用户是否拥有超级管理员权限，默认自己是超级管理员
    :param fromusername: 
    :param tousername: 
    :param wx_remark: 
    :return: 
    """
    if not wx_remark:
        # 判断是否是自己，默认自己为超级管理员
        if fromusername == tousername and fromusername:
            return True
        return False
    cursor.execute('SELECT id, staff_name, branch_id from app_user where is_superuser=1 and wx_remark=?', (wx_remark,))
    result = cursor.fetchone()
    if result:
        return True
    return False


def unauthorized(fromusername):
    itchat.send_msg('无权进行操作', fromusername)


@itchat.msg_register('Text')
def message_repaly(msg):
    nickname = msg['User']['NickName']
    remarkname = msg['User']['RemarkName']
    fromusername = msg['FromUserName']
    tousername = msg['ToUserName']

    # -----------------------普通用户-----------------------
    # 数据汇报
    if fields[5] in msg['Text']:
        # 鉴权
        auth = is_authuser(remarkname)
        if not auth:
            unauthorized(fromusername)
            return
        op_id, op_name, op_branch_id, op_branch_name, op_group_id, op_group_name = auth
        finder = [refind('{0}[:|：] *(\w+)\n*'.format(x), msg['Text']) for x in fields]
        if all(finder):
            staff_name, cust_name, car_no, cust_phone, cust_id, clerk_id, prem = finder
            staff_user = get_userinfo(staff_name)
            if not staff_user:
                return '不存在此员工，请核对员工姓名'
            staff_id, staff_name, branch_id, branch_name, group_id, group_name = staff_user
            cursor.execute(
                'INSERT INTO app_log(staff_id, cust_name, car_no, cust_phone, cust_id, clerk_id, op_at, prem, branch_id, op_user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (staff_id, cust_name, car_no, cust_phone, cust_id, clerk_id, Arrow.now().format('YYYY-MM-DD'), prem,
                 op_branch_id, op_id))
            conn.commit()
            return f'恭喜 {op_name} 成功上传销售数据！ {op_branch_name} 离夺冠又近了一步！'
        return u'格式不对或数据不完整，请直接在聊天窗口对我输入 模版 获取标准格式样本。'

    # 标准模版
    if re.match('模[版板]', msg['Text']):
        auth = is_authuser(remarkname)
        if auth:
            itchat.send_msg('！！请直接复制下面的消息，将数据填到冒号后发回给我，即可完成数据报告。目前必需输入的字段有员工、车主姓名、销售员工号和保费，其余未收集字段，可在冒号后填上“未收集”！！', fromusername)
            return u'\n'.join([k + ': ' for k in fields])

    # 帮助
    if u'帮助' == msg['Text']:
        auth = is_authuser(remarkname)
        if auth:
            return f'[目前有效指令]\n' \
                   f'{sep}' \
                   f'模版  --   获取标准上报模版\n' \
                   f'统计  --   查看本部门完成度\n' \
                   f'详细  --   查看本人报送详细\n' \
                   f'删除 编号  --  删除指定记录\n' \
                   f'{sep}' \
                   f'公司排名  --   全市汇总排名\n' \
                   f'机关排名  --   机关汇总排名\n' \
                   f'竞技之王  --   个人汇总排名\n' \
                   f'{sep}' \
                   f'公司 YYYYMMDD --   公司每日\n' \
                   f'机关 YYYYMMDD --   机关每日\n' \
                   f'十星 YYYYMMDD --   个人每日\n'

    # 本部门信息统计
    if u'统计' == msg['Text']:
        # 鉴权
        auth = is_authuser(remarkname)
        if not auth:
            unauthorized(fromusername)
            return
        op_id, op_name, op_branch_id, op_branch_name, op_group_id, op_group_name = auth
        cursor.execute(
            'select (select pm from total_company_view WHERE group_id = ?) as current_pm,(SELECT MAX(pm) from total_company_view)  as total_pm',
            (op_group_id,))
        curr_rank, total_rank = cursor.fetchone()
        cursor.execute('SELECT dcv.finished, dcv.prem from day_company_view as dcv where dcv.op_at=? and dcv.group_id=?',
                       (Arrow.now().format('YYYY-MM-DD'), op_group_id))
        get_day_score = cursor.fetchone()
        day_finished, day_prem = get_day_score if get_day_score else (0, 0)
        cursor.execute(
            'SELECT sum(tcv.finished) as finished, sum(tcv.prem) as prem from total_company_view as tcv where tcv.group_id=? GROUP BY tcv.group_id',
            (op_group_id,))
        get_total_score = cursor.fetchone()
        total_finished, total_prem = get_total_score
        cursor.execute('select staff_name, finished, sell_target FROM app_user_view WHERE staff_branch_id = ? ORDER BY  finished DESC ', (op_branch_id,))
        rows = cursor.fetchall()
        itchat.send_msg(f'{Arrow.now().format("YYYY-MM-DD")}\n{op_group_name} 全市排名第 {curr_rank}/{total_rank}\n\n'
                        f'[团队战绩]\n{sep}今日销售 {day_finished} 单, 保费 {day_prem} 元\n总计销售 {total_finished} 单, 保费 {total_prem} 元\n'
                        f'\n[{op_branch_name} 各员工完成情况]\n{sep}' + '\n'.join([f'{staff_name:{18-len(staff_name)*3}}{":":^5}{finished}/{sell_target}' for (staff_name, finished, sell_target) in rows]), fromusername)

    # 详细
    if u'详细' == msg['Text']:
        # 鉴权
        auth = is_authuser(remarkname)
        if not auth:
            unauthorized(fromusername)
            return
        op_id, op_name, op_branch_id, op_branch_name, op_group_id, op_group_name = auth
        cursor.execute('select log_id, staff_name, cust_name from app_log_view where op_user_id=? ORDER BY op_at', (op_id,))
        rows = cursor.fetchall()
        return f'[个人上传数据详细]\n{sep}{"编号":8}{"员工":14}{"车主":6}\n{sep}' + \
               '\n'.join([
                   f'{og_id:<{8-len(str(og_id))}}{staff_name:>{12-len(staff_name)*3}}{cust_name:>{16-len(str(cust_name))}}'
                   for (og_id, staff_name, cust_name) in rows])

    # 删除
    del_reg = '删除\s*(\d+)$'
    if re.match(del_reg, msg['Text']):
        log_id = re.findall(del_reg, msg['Text'])[0]
        # 鉴权
        auth = is_authuser(remarkname)
        if not auth:
            unauthorized(fromusername)
            return
        op_id, op_name, op_branch_id, op_branch_name, op_group_id, op_group_name = auth
        # 是否上传者
        cursor.execute('select id from app_log where op_user_id=? and id=?', (op_id, log_id))
        if not cursor.fetchone():
            unauthorized(fromusername)
            return
        cursor.execute('DELETE FROM app_log WHERE id = ?', (log_id,))
        conn.commit()
        return f'成功删除记录'

    # 公司排名
    if u'公司排名' == msg['Text']:
        # 鉴权
        auth = is_authuser(remarkname)
        if not auth:
            unauthorized(fromusername)
            return
        op_id, op_name, op_branch_id, op_branch_name, op_group_id, op_group_name = auth
        cursor.execute('SELECT pm, group_id, group_name, prem, finished, target from total_company_view')
        rows = cursor.fetchall()
        return f'[全市机构排名 - 总计]\n{Arrow.now().format("YYYY-MM-DD")}\n{sep}{"#":4}{"机构":10}{"完成":4}{"目标":6}保费\n{sep}' + \
               '\n'.join([
                             f'{pm:<{5-len(str(pm))}}{group_id:{14-len(group_id)*3}}{row[4]:>{8-len(str(row[4]))}}{row[5]:>{10-len(str(row[5]))}}{row[3]:>{14-len(str(row[3]))}}'
                             for (pm, group_id, group_name, prem, finished, target) in rows])

    # 机关排名
    if u'机关排名' == msg['Text']:
        # 鉴权
        auth = is_authuser(remarkname)
        if not auth:
            unauthorized(fromusername)
            return
        op_id, op_name, op_branch_id, op_branch_name, op_group_id, op_group_name = auth
        cursor.execute('SELECT pm, branch_name, finished, target, prem from total_dept_view;')
        rows = cursor.fetchall()
        return f'[市公司机关排名 - 总计]\n{Arrow.now().format("YYYY-MM-DD")}\n{sep}{"#":4}{"单位":10}{"完成":4}{"目标":6}保费\n{sep}' + \
               '\n'.join([
                             f'{row[0]:<{5-len(str(row[0]))}}{row[1]:{16-len(row[1])*3}}{row[2]:>{6-len(str(row[2]))}}{row[3]:>{8-len(str(row[3]))}}{row[4]:>{14-len(str(row[4]))}}'
                             for row in rows])

    # 竞技之王
    if u'竞技之王' == msg['Text']:
        # 鉴权
        auth = is_authuser(remarkname)
        if not auth:
            unauthorized(fromusername)
            return
        op_id, op_name, op_branch_id, op_branch_name, op_group_id, op_group_name = auth
        cursor.execute('SELECT staff_name, branch_name, finished, prem from total_person_view;')
        rows = cursor.fetchall()
        return f'[全市个人销售前8 - 总计]\n{Arrow.now().format("YYYY-MM-DD")}\n{sep}{"姓名":10}{"单位":10}{"完成":4}保费\n{sep}' + \
               '\n'.join([
                             f'{row[0]:<{16-len(row[0])*3}}{row[1]:{20-len(row[1])*3}}{row[2]:<{8-len(str(row[2]))}}{row[3]:>{8-len(str(row[3]))}}'
                             for row in rows])

    # 公司 日期
    day_comp = '公司\s*(\d{4}\-*\d{2}-*\d{2})$'
    if re.match(day_comp, msg['Text']):
        input_date = re.findall(day_comp, msg['Text'])[0]
        # 鉴权
        auth = is_authuser(remarkname)
        if not auth:
            unauthorized(fromusername)
            return
        op_id, op_name, op_branch_id, op_branch_name, op_group_id, op_group_name = auth
        cursor.execute(
            'SELECT group_name, finished, prem from day_company_view WHERE op_at=? ORDER BY prem desc, finished desc;',
            (input_date,))
        rows = cursor.fetchall()
        return f'[全市机构销售 - 每日]\n{input_date}\n{sep}{"机构":16}{"完成":8}保费\n{sep}' + \
               '\n'.join(
                   [f'{group_name:{24-len(group_name)*3}}{finished:>{8-len(str(finished))}}{prem:>{15-len(str(prem))}}'
                    for (group_name, finished, prem) in rows])

    # 机关 日期
    day_dept = '机关\s*(\d{4}\-*\d{2}-*\d{2})$'
    if re.match(day_dept, msg['Text']):
        input_date = re.findall(day_dept, msg['Text'])[0]
        # 鉴权
        auth = is_authuser(remarkname)
        if not auth:
            unauthorized(fromusername)
            return
        op_id, op_name, op_branch_id, op_branch_name, op_group_id, op_group_name = auth
        cursor.execute(
            'select branch_name, finished, prem from day_dept_view WHERE op_at=? ORDER BY prem desc, finished desc;',
            (input_date,))
        rows = cursor.fetchall()
        return f'[市公司机关销售 - 每日]\n{input_date}\n{sep}{"单位":16}{"完成":8}保费\n{sep}' + \
               '\n'.join([
                             f'{branch_name:{20-len(branch_name)*3}}{finished:>{8-len(str(finished))}}{prem:>{15-len(str(prem))}}'
                             for (branch_name, finished, prem) in rows])

    # 十星 日期
    top_10 = '十星\s*(\d{4}\-*\d{2}-*\d{2})$'
    if re.match(top_10, msg['Text']):
        input_date = re.findall(top_10, msg['Text'])[0]
        # 鉴权
        auth = is_authuser(remarkname)
        if not auth:
            unauthorized(fromusername)
            return
        op_id, op_name, op_branch_id, op_branch_name, op_group_id, op_group_name = auth
        cursor.execute(
            'select top 10 staff_name, branch_name, finished, prem from day_person_view WHERE op_at=? ORDER BY prem desc, finished desc',
            (input_date,))
        rows = cursor.fetchall()
        return f'[全市个人销售前十 - 每日]\n{input_date}\n{sep}{"姓名":8}{"单位":10}{"完成":4}保费\n{sep}' + \
               '\n'.join([
                   f'{staff_name:{14-len(staff_name)*3}}{branch_name:{16-len(branch_name)*3}}{finished:>{8-len(str(finished))}}{prem:>{10-len(str(prem))}}'
                   for (staff_name, branch_name, finished, prem) in rows])

        # TODO 导出(需要超级管理员权限)
        # TODO 开通用户使用权（需要超级管理员权限）

        # 全局默认回复
        # return u'对我输入 帮助 可以获得魔法效果'


if __name__ == '__main__':
    itchat.auto_login(hotReload=True)
    friends = itchat.get_friends()
    chatrooms = itchat.get_chatrooms()

    itchat.run()
