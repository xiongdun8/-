"""
使用前须知：
arrange_hexagram(original_hexagram, time, reason)函数为本模块关键函数，返回值为排盘所有内容。
具体调用方法可参考github说明或下载的md文档文件
若要使用AI解析功能，请更改Deepseek APIkey值（约在代码540行处）
ai_text变量存储了向ai提问的必要文本（即省略了相关备忘信息和分割线，以便节省tokens）
"""

import datetime
import dizhi  # 时间地支转换模块
import guagong  # 卦宫判断模块
import wangshuai  # 旺衰判断模块
import data  # 卦辞和爻辞存储模块
import ai_main  # 调用deepseek-chat 模块

# ---------------------- 六爻核心配置数据 ----------------------
HEXAGRAM_EARTHLY_BRANCH = {
    "乾宫": ["子", "寅", "辰", "午", "申", "戌"],
    "坤宫": ["未", "巳", "卯", "丑", "亥", "酉"],
    "震宫": ["子", "寅", "辰", "午", "申", "戌"],
    "巽宫": ["丑", "亥", "酉", "未", "巳", "卯"],
    "坎宫": ["寅", "辰", "午", "申", "戌", "子"],
    "离宫": ["卯", "丑", "亥", "酉", "未", "巳"],
    "艮宫": ["辰", "午", "申", "戌", "子", "寅"],
    "兑宫": ["巳", "卯", "丑", "亥", "酉", "未"]
}

BRANCH_WUXING = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水"
}

LIUSHOU = ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"]

# 旬空计算所需配置
XUN_START = ["甲子", "甲戌", "甲申", "甲午", "甲辰", "甲寅"]
XUN_END = ["癸酉", "癸未", "癸巳", "癸卯", "癸丑", "癸亥"]
XUN_KONG = {
    "甲子": ["戌", "亥"],
    "甲戌": ["申", "酉"],
    "甲申": ["午", "未"],
    "甲午": ["辰", "巳"],
    "甲辰": ["寅", "卯"],
    "甲寅": ["子", "丑"]
}
GAN_ORDER = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI_ORDER = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]


# ---------------------- 计算日天干的函数 ----------------------
def get_day_stem(year, month, day):
    """根据日期计算日天干（以1900年1月1日庚子日为基准）"""
    base_date = datetime.date(1900, 1, 1)
    target_date = datetime.date(year, month, day)
    delta_days = (target_date - base_date).days
    base_gan_index = 6  # 1900年1月1日是庚子日，天干为"庚"
    gan_index = (base_gan_index + delta_days) % 10
    return GAN_ORDER[gan_index]


# ---------------------- 旬空计算函数 ----------------------
def get_xunkong(day_ganzhi):
    day_gan = day_ganzhi[0]
    day_zhi = day_ganzhi[1]
    day_gan_idx = GAN_ORDER.index(day_gan)
    day_zhi_idx = ZHI_ORDER.index(day_zhi)
    day_total_idx = day_gan_idx * 12 + day_zhi_idx

    for i in range(len(XUN_START)):
        start_gan = XUN_START[i][0]
        start_zhi = XUN_START[i][1]
        end_gan = XUN_END[i][0]
        end_zhi = XUN_END[i][1]

        start_gan_idx = GAN_ORDER.index(start_gan)
        start_zhi_idx = ZHI_ORDER.index(start_zhi)
        start_total_idx = start_gan_idx * 12 + start_zhi_idx

        end_gan_idx = GAN_ORDER.index(end_gan)
        end_zhi_idx = ZHI_ORDER.index(end_zhi)
        end_total_idx = end_gan_idx * 12 + end_zhi_idx

        if i == len(XUN_START) - 1:  # 甲寅旬特殊处理
            if day_total_idx >= start_total_idx or day_total_idx <= end_total_idx:
                return XUN_KONG[XUN_START[i]]
        else:
            if start_total_idx <= day_total_idx <= end_total_idx:
                return XUN_KONG[XUN_START[i]]
    return ["", ""]  # 理论上不会触发


def get_liqin(wo_wuxing, target_wuxing):
    if not wo_wuxing or not target_wuxing:
        return ""
    if target_wuxing == wo_wuxing:
        return "兄弟"
    elif (wo_wuxing == "木" and target_wuxing == "水") or \
            (wo_wuxing == "火" and target_wuxing == "木") or \
            (wo_wuxing == "土" and target_wuxing == "火") or \
            (wo_wuxing == "金" and target_wuxing == "土") or \
            (wo_wuxing == "水" and target_wuxing == "金"):
        return "父母"
    elif (wo_wuxing == "木" and target_wuxing == "火") or \
            (wo_wuxing == "火" and target_wuxing == "土") or \
            (wo_wuxing == "土" and target_wuxing == "金") or \
            (wo_wuxing == "金" and target_wuxing == "水") or \
            (wo_wuxing == "水" and target_wuxing == "木"):
        return "子孙"
    elif (wo_wuxing == "木" and target_wuxing == "金") or \
            (wo_wuxing == "火" and target_wuxing == "水") or \
            (wo_wuxing == "土" and target_wuxing == "木") or \
            (wo_wuxing == "金" and target_wuxing == "火") or \
            (wo_wuxing == "水" and target_wuxing == "土"):
        return "官鬼"
    else:
        return "妻财"


# ---------------------- 入墓扩展判断 ----------------------
def check_additional_tomb(original_hexagram, original_branch, changed_branch, strengths, is_original=True):
    positions = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"]
    moving_indices = [i for i, line in enumerate(original_hexagram) if line in [3, 4]]

    for i in range(6):
        yao_branch = original_branch[i] if is_original else changed_branch[i]
        yao_wuxing = BRANCH_WUXING[yao_branch]
        tomb_branches = wangshuai.TOMB_BRANCH[yao_wuxing]
        if not isinstance(tomb_branches, list):
            tomb_branches = [tomb_branches]

        if is_original and original_hexagram[i] not in [3, 4]:  # 静爻
            for idx in moving_indices:
                mb = original_branch[idx]
                if mb in tomb_branches:
                    strengths[i]["status"].append(f"入{positions[idx]}墓")

        if is_original and original_hexagram[i] in [3, 4]:  # 动爻
            if changed_branch and i < len(changed_branch):
                changed_yao = changed_branch[i]
                if changed_yao in tomb_branches:
                    strengths[i]["status"].append("入变爻墓")

        if not is_original and i in moving_indices:  # 变卦中对应本卦动爻的位置
            original_yao = original_branch[i]
            if original_yao in tomb_branches:
                strengths[i]["status"].append("入本位动爻墓")
    return strengths


# ---------------------- 回头生克判断 ----------------------
def check_huitou(original_branch, changed_branch, moving_indices, changed_strength):
    for i in moving_indices:
        original_wuxing = BRANCH_WUXING[original_branch[i]]
        changed_wuxing = BRANCH_WUXING[changed_branch[i]]
        if wangshuai.GENERATE_WUXING.get(changed_wuxing) == original_wuxing:
            changed_strength[i]["status"].append("回头生")
        if wangshuai.CONQUER_WUXING.get(changed_wuxing) == original_wuxing:
            changed_strength[i]["status"].append("回头克")
    return changed_strength


# ---------------------- 主程序功能 ----------------------
def get_user_input():
    print("六爻排盘程序（含纳甲、六兽、六亲、旺衰）")
    print("请输入起卦原因：")
    reason = input().strip()

    print("\n卦象编码：1=少阴，2=少阳，3=纯阳（动爻），4=纯阴（动爻）")
    print("请输入6爻（从初爻到上爻，用空格分隔）：")

    while True:
        try:
            hexagram_input = input("输入6个数字（1-4）：").strip()
            hexagram = [int(num) for num in hexagram_input.split()]
            if len(hexagram) != 6:
                print("需输入6个数字，请重新输入！")
                continue
            for num in hexagram:
                if num not in [1, 2, 3, 4]:
                    raise ValueError
            break
        except ValueError:
            print("输入错误，仅支持1-4的数字，用空格分隔！")

    now = datetime.datetime.now()
    print(f"\n当前时间：{now.year}年{now.month}月{now.day}日 {now.hour}:{now.minute}")
    use_current = input("是否使用当前时间？(y/n)：").strip().lower()

    if use_current != 'y':
        while True:
            try:
                year = int(input("年份："))
                month = int(input("月份："))
                day = int(input("日期："))
                hour = int(input("小时（0-23）："))
                minute = int(input("分钟："))
                now = datetime.datetime(year, month, day, hour, minute)
                break
            except ValueError:
                print("时间格式错误，请重新输入！")

    return hexagram, now, reason


def generate_changed_hexagram(original):
    """修正动爻转换规则：纯阳(3)变少阴(1)，纯阴(4)变少阳(2)"""
    changed = []
    for line in original:
        if line == 3:  # 纯阳动爻变为少阴
            changed.append(1)
        elif line == 4:  # 纯阴动爻变为少阳
            changed.append(2)
        else:  # 静爻不变
            changed.append(line)

    # 验证变卦是否真的发生变化
    if changed == original:
        for i in range(len(changed)):
            if original[i] in [3, 4]:  # 找到动爻位置强制转换
                changed[i] = 2 if original[i] == 3 else 1
                break
    return changed


def get_liushou_order(day_branch):
    branch_order = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    day_idx = branch_order.index(day_branch)
    start_idx = day_idx % 6
    return [LIUSHOU[(start_idx + i) % 6] for i in range(6)]


ai_text = ""  #初始化全局变量ai_text


def arrange_hexagram(original_hexagram, time, reason):
    # 初始化存储完整输出的变量
    ai_txt = []
    full_txt = []
    positions = ["初爻", "二爻", "三爻", "四爻", "五爻", "上爻"]
    line_names = {1: "少阴", 2: "少阳", 3: "纯阳", 4: "纯阴"}
    line_symbols = {
        1: "-- --",  # 少阴
        2: "-----",  # 少阳
        3: "-----",  # 纯阳（动）
        4: "-- --"  # 纯阴（动）
    }
    moving_marks = {3: "  →", 4: "  →", 1: "   ", 2: "   "}

    # 1. 计算时间地支和旬空
    year_branch = dizhi.LunarToEarthlyBranch.get_year_branch(time.year)
    month_branch = dizhi.LunarToEarthlyBranch.get_month_branch(time.year, time.month, time.day)
    day_branch = dizhi.LunarToEarthlyBranch.get_day_branch(time.year, time.month, time.day)
    day_stem = get_day_stem(time.year, time.month, time.day)
    day_ganzhi = day_stem + day_branch  # 日干支
    xunkong = get_xunkong(day_ganzhi)  # 计算旬空
    hour_branch = dizhi.LunarToEarthlyBranch.get_hour_branch(time.hour)

    # 2. 六兽顺序
    liushou_order = get_liushou_order(day_branch)

    # 3. 本卦信息
    original_info = guagong.get_hexagram_palace(original_hexagram)
    original_type = original_info["宫名"]
    original_hex_name = original_info["卦名"]
    original_branch = HEXAGRAM_EARTHLY_BRANCH[original_type]

    # 4. 变卦信息
    has_moving = any(line in [3, 4] for line in original_hexagram)
    changed_hexagram = generate_changed_hexagram(original_hexagram) if has_moving else None

    # 强制验证变卦是否与本卦不同
    if has_moving and changed_hexagram == original_hexagram:
        full_txt.append("\n警告：检测到变卦与本卦完全相同，已尝试重新修正")
        print("\n警告：检测到变卦与本卦完全相同，已尝试重新修正！")
        for i in range(len(changed_hexagram)):
            if original_hexagram[i] == 3:
                changed_hexagram[i] = 2
                break
            elif original_hexagram[i] == 4:
                changed_hexagram[i] = 1
                break

    # 重新获取变卦信息
    changed_info = guagong.get_hexagram_palace(changed_hexagram) if (has_moving and changed_hexagram) else None
    changed_type = changed_info["宫名"] if (has_moving and changed_info) else None
    changed_hex_name = changed_info["卦名"] if (has_moving and changed_info) else None
    changed_branch = HEXAGRAM_EARTHLY_BRANCH[changed_type] if (has_moving and changed_type) else None

    # 5. 世应爻
    shi_yao_idx = original_info["世爻索引"]
    shi_yao_branch = original_branch[shi_yao_idx]
    shi_yao_wuxing = BRANCH_WUXING[shi_yao_branch]
    ying_yao_idx = original_info["应爻索引"]
    ying_yao_branch = original_branch[ying_yao_idx]

    changed_shi_yao_idx = changed_info["世爻索引"] if (has_moving and changed_info) else None
    changed_shi_yao_branch = changed_branch[changed_shi_yao_idx] if (
            has_moving and changed_branch and changed_shi_yao_idx is not None) else None
    changed_shi_yao_wuxing = BRANCH_WUXING[changed_shi_yao_branch] if (has_moving and changed_shi_yao_branch) else None

    # 标记动爻
    is_moving_original = [line in [3, 4] for line in original_hexagram]
    moving_indices = [i for i, is_moving in enumerate(is_moving_original) if is_moving]

    # 6. 计算旺衰
    original_strength = wangshuai.batch_calculate_strength(
        yao_branches=original_branch,
        month_branch=month_branch,
        day_branch=day_branch,
        changed_branches=changed_branch,
        is_moving_yaos=is_moving_original
    )

    original_strength = check_additional_tomb(
        original_hexagram=original_hexagram,
        original_branch=original_branch,
        changed_branch=changed_branch,
        strengths=original_strength,
        is_original=True
    )

    changed_strength = None
    if has_moving and changed_hexagram and changed_branch:
        changed_strength = wangshuai.batch_calculate_strength(
            yao_branches=changed_branch,
            month_branch=month_branch,
            day_branch=day_branch,
            changed_branches=None
        )

        changed_strength = check_additional_tomb(
            original_hexagram=original_hexagram,
            original_branch=original_branch,
            changed_branch=changed_branch,
            strengths=changed_strength,
            is_original=False
        )

        changed_strength = check_huitou(
            original_branch=original_branch,
            changed_branch=changed_branch,
            moving_indices=moving_indices,
            changed_strength=changed_strength
        )

    # 7. 输出头部信息
    header_line1 = "\n" + "=" * 140
    full_txt.append(header_line1)
    ai_txt.append(header_line1)
    print(header_line1)

    header_line2 = f"排盘时间：{time.year}年{time.month}月{time.day}日 {time.hour}:{time.minute}"
    full_txt.append(header_line2)
    ai_txt.append(header_line2)
    print(header_line2)

    header_line2_5 = f"起卦原因：{reason}"
    ai_txt.append(header_line2_5)
    full_txt.append(header_line2_5)
    print(header_line2_5)

    header_line3 = f"地支：年{year_branch} 月{month_branch} 日{day_branch} 时{hour_branch}"
    full_txt.append(header_line3)
    ai_txt.append(header_line3)
    print(header_line3)

    header_line4 = f"旬空：{xunkong[0]}{xunkong[1]}空"
    full_txt.append(header_line4)
    ai_txt.append(header_line4)
    print(header_line4)

    header_line5 = f"本卦：{original_type}{original_info['卦类型']}（{original_hex_name}）  世爻：{positions[shi_yao_idx]}({shi_yao_branch})  应爻：{positions[ying_yao_idx]}({ying_yao_branch})"
    full_txt.append(header_line5)
    ai_txt.append(header_line5)
    print(header_line5)

    if has_moving and changed_type and changed_hex_name:
        header_line6 = f"变卦：{changed_type}{changed_info['卦类型']}（{changed_hex_name}）  世爻：{positions[changed_shi_yao_idx]}({changed_shi_yao_branch})" if changed_shi_yao_idx is not None else f"变卦：{changed_type}{changed_info['卦类型']}（{changed_hex_name}）"
        full_txt.append(header_line6)
        ai_txt.append(header_line6)
        print(header_line6)

    header_line7 = "=" * 140
    ai_txt.append(header_line7)
    full_txt.append(header_line7)
    print(header_line7)

    # 8. 输出本卦（从上爻到初爻）
    bengua_title = "\n【本卦】"
    full_txt.append(bengua_title)
    ai_txt.append(bengua_title)
    print(bengua_title)

    # 打印表头
    header = "六兽       六亲        爻位      世应（+为世）卦象         地支(五行)          类型           旺衰得分            状态"
    full_txt.append(header)
    ai_txt.append(header)
    print(header)
    full_txt.append("-" * 140)
    ai_txt.append("-" * 140)
    print("-" * 140)

    # 从上爻(5)到初爻(0)输出
    for i in range(5, -1, -1):
        line_value = original_hexagram[i]
        beast = liushou_order[i]
        branch = original_branch[i]
        wuxing = BRANCH_WUXING[branch]
        liqin = get_liqin(shi_yao_wuxing, wuxing)
        strength = original_strength[i]

        # 世应标识和间距
        if i == shi_yao_idx:
            shiying = " + "
            spacing = "\u200A"
        elif i == ying_yao_idx:
            shiying = " * "
            spacing = "\u200A"
        else:
            shiying = "---"
            spacing = "\u200A"

        status_text = "、".join(strength["status"]) if strength["status"] else "无"
        guaxiang = f"{spacing}{line_symbols[line_value]}{moving_marks[line_value]}"

        yao_line = "{0:8} {1:8} {2:8} {3:8} {4:15} {5:15} {6:12} 旺衰得分：{7:<6} 状态：{8}".format(
            beast, liqin, positions[i], shiying, guaxiang,
            f"{branch}({wuxing})", line_names[line_value],
            str(strength['score']), status_text
        )
        full_txt.append(yao_line)
        ai_txt.append(yao_line)
        print(yao_line)

    # 9. 输出变卦（从上爻到初爻）
    if has_moving and changed_hexagram and changed_strength:
        biangua_title = "\n【变卦】"
        full_txt.append(biangua_title)
        ai_txt.append(biangua_title)
        print(biangua_title)

        full_txt.append(header)
        ai_txt.append(header)
        print(header)
        full_txt.append("-" * 140)
        ai_txt.append("-" * 140)
        print("-" * 140)

        # 从上爻(5)到初爻(0)输出
        for i in range(5, -1, -1):
            line_value = changed_hexagram[i]
            beast = liushou_order[i]
            branch = changed_branch[i]
            wuxing = BRANCH_WUXING[branch]
            liqin = get_liqin(changed_shi_yao_wuxing, wuxing) if changed_shi_yao_wuxing else ""
            strength = changed_strength[i]

            # 世应标识和间距
            if changed_shi_yao_idx is not None and i == changed_shi_yao_idx:
                shiying = " + "
                spacing = "\u200A"
            elif changed_shi_yao_idx is not None and i == (changed_shi_yao_idx + 3) % 6:
                shiying = " * "
                spacing = "\u200A"
            else:
                shiying = "---"
                spacing = "\u200A"

            status_text = "、".join(strength["status"]) if strength["status"] else "无"
            guaxiang = f"{spacing}{line_symbols[line_value]}   "

            yao_line = "{0:8} {1:8} {2:8} {3:8} {4:15} {5:15} {6:12} 旺衰得分：{7:<6} 状态：{8}".format(
                beast, liqin, positions[i], shiying, guaxiang,
                f"{branch}({wuxing})", line_names[line_value],
                str(strength['score']), status_text
            )
            full_txt.append(yao_line)
            ai_txt.append(yao_line)
            print(yao_line)

    # 10. 动爻汇总
    moving_lines = [i + 1 for i, line in enumerate(original_hexagram) if line in [3, 4]]
    if moving_lines:
        moving_line = f"\n动爻汇总：{', '.join(map(str, moving_lines))}爻"
    else:
        moving_line = "\n无动爻（纯净卦）"
    full_txt.append(moving_line)
    ai_txt.append(moving_line)
    print(moving_line)

    # 11. 卦辞爻辞
    guaci_line = "\n" + "=" * 140
    full_txt.append(guaci_line)
    print(guaci_line)

    guamin_text = data.get_hexagram_texts(original_hex_name)
    guaming_line = '\n本卦卦名：' + original_hex_name
    full_txt.append(guaming_line)
    print(guaming_line)

    guaci_line = "卦辞：" + guamin_text["卦辞"]
    full_txt.append(guaci_line)
    print(guaci_line)

    for i in range(6):
        yaoci_line = guamin_text["爻辞"][i]
        full_txt.append(yaoci_line)
        print(yaoci_line)

    #  备忘打印
    name_beiwang = """\n============================================================================================================================================
\n地支相合：子丑合土局（水）; 寅亥合木局;卯戌合火局; 辰酉合金局; 巳申合水局; 午未合土局
地支相冲：子午；丑未；寅申；卯酉；辰戌；巳亥
木长生在亥，旺在卯，墓在未，绝于申；
金长生在巳，旺在酉，墓在丑，绝于寅；
火长生在寅，旺在午，墓在戌，绝于亥；
水长生在申，旺在子，墓在辰，绝于巳；
土随火行：长生在寅，绝于亥；墓于四墓库，旺于四墓库

    季节    旺  相  休  囚  死
    春季    木  火  水  金  土
    夏季    火  土  木  水  金
    秋季    金  水  土  火  木
    冬季    水  木  金  土  火
    季末    土  金  火  木  水 """
    full_txt.append(name_beiwang)
    print(name_beiwang)

    shenmin = "\n旺衰得分仅作最基础参考"
    full_txt.append(shenmin)
    print(shenmin)

    global ai_text
    ai_text = '\n'.join(ai_txt)  # 合并为完整字符串（ai提问文档）
    full_text = '\n'.join(full_txt)  # 合并为完整字符串并返回
    return full_text

# ---------------------- AI解析模块 ----------------------
def ai_word(ask):
    api_key = "sk-********************************"  #填写你自己的deepseek APIkey（基于deepseek文档开发，其他AI接口可能不兼容）

    print("\n========== 以下为AI解析 ==========")
    try:
        # 调用AI接口
        response = ai_main.deepseek_chat(
            api_key=api_key,
            prompt=ask,
            max_tokens=1500,
            stream=True
        )

        # 先判断返回是否为字符串（完整响应）
        if isinstance(response, str):
            print(response)
            print("\n=== AI解析结束 ===")
            return

        # 流式输出处理（如果是迭代器）
        full_content = []
        for chunk in response:
            # 检查chunk是否为字典类型
            if not isinstance(chunk, dict):
                # 直接输出非字典类型的内容（如字符串）
                print(chunk, end='', flush=True)
                full_content.append(str(chunk))
                continue

            if "error" in chunk:
                print(f"AI调用错误: {chunk['error']}")
                return
            # 提取流式内容（根据实际API返回格式调整）
            content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
            if content:
                print(content, end='', flush=True)  # 实时输出
                full_content.append(content)
        print("\n=== AI解析结束 ===")
    except Exception as e:
        print(f"AI解析过程出错：{str(e)}")



# ------------------- 主程序入口 -------------------
if __name__ == "__main__":
    original_hexagram, time, reason = get_user_input()
    arrange_hexagram(original_hexagram, time, reason)
    # 询问用户是否使用AI解析
    use_ai = input("\n是否使用AI解析排盘结果？(y/n)：").strip().lower()
    if use_ai in ['y', 'yes']:
        # 构造AI询问内容
        prompt = f"请对以下六爻排盘信息进行解析：\n{ai_text}"  # 填写向ai提问的内容(存储在ai_text)
        ai_word(prompt)
    else:
        print("\n程序结束，未使用AI解析功能。")