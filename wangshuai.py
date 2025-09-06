# p4模块：六爻爻旺衰判断核心模块
# 功能：计算每一爻的旺衰得分及状态（月扶、日生、入墓、暗动等）

# 地支五行对应表
BRANCH_WUXING = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水"
}

# 地支相冲关系（对宫相冲）
CONFLICT_BRANCH = {
    "子": "午", "午": "子",
    "丑": "未", "未": "丑",
    "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰",
    "巳": "亥", "亥": "巳"
}

# 地支相合关系
COMBINE_BRANCH = {
    "子": "丑", "丑": "子",
    "寅": "亥", "亥": "寅",
    "卯": "戌", "戌": "卯",
    "辰": "酉", "酉": "辰",
    "巳": "申", "申": "巳",
    "午": "未", "未": "午"
}

# 入墓规则（爻五行对应墓库地支）
TOMB_BRANCH = {
    "木": "未",  # 木入未墓
    "火": "戌",  # 火入戌墓
    "金": "丑",  # 金入丑墓
    "水": "辰",  # 水入辰墓
    "土": ["辰", "戌", "丑", "未"]  # 土入四墓库
}

# 五行生克关系
GENERATE_WUXING = {  # 生者→被生者
    "木": "火",
    "火": "土",
    "土": "金",
    "金": "水",
    "水": "木"
}

CONQUER_WUXING = {  # 克者→被克者
    "木": "土",
    "土": "水",
    "水": "火",
    "火": "金",
    "金": "木"
}

# 长生十二宫-帝旺位（仅用于日令判断）
IMPERIAL_WANG = {
    "木": "卯",
    "火": "午",
    "金": "酉",
    "水": "子",
    "土": ["辰", "戌", "丑", "未"]  # 土帝旺于四墓库
}

# 长生十二宫-绝位
EXTINCTION = {
    "木": "申",  # 木绝于申
    "火": "亥",  # 火绝于亥
    "金": "寅",  # 金绝于寅
    "水": "巳",  # 水绝于巳
    "土": "亥"  # 土随火行，绝于亥
}


def get_seasonal_status(month_branch):
    """根据月令地支判断五行四季状态（旺相休囚死）"""
    if month_branch in ["寅", "卯"]:  # 春季
        return {"木": "旺", "火": "相", "水": "休", "金": "囚", "土": "死"}
    elif month_branch in ["巳", "午"]:  # 夏季
        return {"火": "旺", "土": "相", "木": "休", "水": "囚", "金": "死"}
    elif month_branch in ["申", "酉"]:  # 秋季
        return {"金": "旺", "水": "相", "土": "休", "火": "囚", "木": "死"}
    elif month_branch in ["亥", "子"]:  # 冬季
        return {"水": "旺", "木": "相", "金": "休", "土": "囚", "火": "死"}
    elif month_branch in ["辰", "未", "戌", "丑"]:  # 四季末（土旺）
        return {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"}
    return {}  # 异常月份默认空


def calculate_yao_strength(yao_branch, month_branch, day_branch, changed_yao_branch=None, is_moving_yao=False):
    """计算单爻旺衰得分及状态"""
    score = 0.0
    status = []  # 存储状态术语（如月扶、日生、入墓等）
    yao_wuxing = BRANCH_WUXING[yao_branch]
    month_wuxing = BRANCH_WUXING[month_branch]
    day_wuxing = BRANCH_WUXING[day_branch]

    # ---------------------- 基础得分计算 ----------------------
    # 1. 月建/日建（地支相同）
    if yao_branch == month_branch:
        score += 2.0
        status.append("月建")
    if yao_branch == day_branch:
        score += 1.5
        status.append("日建")

    # 2. 月合相关（合旺/合克）
    if COMBINE_BRANCH.get(yao_branch) == month_branch:
        month_克_yao = CONQUER_WUXING.get(month_wuxing) == yao_wuxing
        yao_克_month = CONQUER_WUXING.get(yao_wuxing) == month_wuxing
        if not (month_克_yao or yao_克_month):
            score += 1.5
            status.append("合旺")
        else:
            score -= 0.5
            status.append("月合克")

    # 3. 日合相关（合绊/合克）
    if COMBINE_BRANCH.get(yao_branch) == day_branch:
        day_克_yao = CONQUER_WUXING.get(day_wuxing) == yao_wuxing
        yao_克_day = CONQUER_WUXING.get(yao_wuxing) == day_wuxing
        if not (day_克_yao or yao_克_day):
            score += 1.5
            status.append("合绊")
        else:
            score -= 0.5
            status.append("日合克")

    # 4. 月生/日生（月令/日令生爻）
    if GENERATE_WUXING.get(month_wuxing) == yao_wuxing:
        score += 1.5
        status.append("月生")
    if GENERATE_WUXING.get(day_wuxing) == yao_wuxing:
        score += 1.5
        status.append("日生")

    # 5. 月扶/日扶（五行相同但地支不同）
    if month_wuxing == yao_wuxing and yao_branch != month_branch:
        score += 1.0
        status.append("月扶")
    if day_wuxing == yao_wuxing and yao_branch != day_branch:
        score += 0.5
        status.append("日扶")

    # 6. 月破（与月相冲）
    if CONFLICT_BRANCH.get(yao_branch) == month_branch:
        score -= 2.0
        status.append("月破")

    # 7. 月克/日克（五行相克）
    if CONQUER_WUXING.get(month_wuxing) == yao_wuxing:
        score -= 1.0
        status.append("月克")
    if CONQUER_WUXING.get(day_wuxing) == yao_wuxing:
        score -= 1.0
        status.append("日克")

    # 8. 日散（与日相冲且不旺）
    is_day_conflict = CONFLICT_BRANCH.get(yao_branch) == day_branch
    if is_day_conflict and score < 0:
        score -= 1.5
        status.append("日散")

    # ---------------------- 新增核心功能 ----------------------
    # 1. 帝旺（日令为爻的帝旺位）
    diwang_branches = IMPERIAL_WANG[yao_wuxing]
    if not isinstance(diwang_branches, list):
        diwang_branches = [diwang_branches]
    if day_branch in diwang_branches:
        score += 1.0
        status.append("帝旺")

    # 2. 季节休囚（根据四季判断休/囚/死）
    seasonal_status = get_seasonal_status(month_branch)
    yao_season = seasonal_status.get(yao_wuxing)
    if yao_season in ["休", "囚", "死"]:
        score -= 1.5
        status.append(f"休囚（{yao_season}）")

    # 3. 入墓（月墓/日墓）
    tomb_branches = TOMB_BRANCH[yao_wuxing]
    if not isinstance(tomb_branches, list):
        tomb_branches = [tomb_branches]
    tomb_source = []
    if month_branch in tomb_branches:
        tomb_source.append("月墓")
    if day_branch in tomb_branches:
        tomb_source.append("日墓")
    if tomb_source:
        score = -0.1  # 入墓固定得分
        status.append(f"入{'/'.join(tomb_source)}")

    # 4. 绝地（静爻处于日令绝位）
    if not is_moving_yao:
        if day_branch == EXTINCTION[yao_wuxing]:
            score -= 0.5
            status.append("绝地")

    # 5. 化绝（动爻化出绝位变爻）
    if changed_yao_branch and is_moving_yao:
        if changed_yao_branch == EXTINCTION[yao_wuxing]:
            score -= 1.0
            status.append("化绝")

    # 6. 暗动（与日相冲且得分≥0）
    if is_day_conflict and score >= 0:
        status.append("暗动")

    # 保留两位小数
    score = round(score, 2)
    return {"score": score, "status": status}


def batch_calculate_strength(yao_branches, month_branch, day_branch, changed_branches=None, is_moving_yaos=None):
    """批量计算六爻旺衰（本卦/变卦）"""
    results = []
    changed_branches = changed_branches or [None] * 6
    is_moving_yaos = is_moving_yaos or [False] * 6  # 动爻标记列表，默认都是静爻
    for i in range(6):
        yao_branch = yao_branches[i]
        changed_yao = changed_branches[i] if i < len(changed_branches) else None
        is_moving = is_moving_yaos[i] if i < len(is_moving_yaos) else False
        result = calculate_yao_strength(
            yao_branch=yao_branch,
            month_branch=month_branch,
            day_branch=day_branch,
            changed_yao_branch=changed_yao,
            is_moving_yao=is_moving
        )
        results.append(result)
    return results