import datetime
# ---------------------- 地支转换核心模块 ----------------------
class LunarToEarthlyBranch:
    """精确计算年月日时对应的地支"""

    EARTHLY_BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

    @staticmethod
    def get_year_branch(year):
        """计算年份地支（以1900年庚子年为基准）"""
        base_year = 1900
        offset = (year - base_year) % 12
        return LunarToEarthlyBranch.EARTHLY_BRANCHES[offset]

    @staticmethod
    def get_month_branch(year, month, day):
        """计算月份地支（结合节气分界）"""
        # 节气表：(月份, 日期)，对应农历月份的起始节气
        solar_terms = [
            (2, 4),  # 寅月（正月）：立春
            (3, 6),  # 卯月（二月）：惊蛰
            (4, 5),  # 辰月（三月）：清明
            (5, 6),  # 巳月（四月）：立夏
            (6, 6),  # 午月（五月）：芒种
            (7, 7),  # 未月（六月）：小暑
            (8, 8),  # 申月（七月）：立秋
            (9, 8),  # 酉月（八月）：白露
            (10, 8),  # 戌月（九月）：寒露
            (11, 7),  # 亥月（十月）：立冬
            (12, 7),  # 子月（十一月）：大雪
            (1, 6)  # 丑月（十二月）：小寒
        ]

        if month == 1:
            # 1月需判断是否过小寒
            term_month, term_day = solar_terms[11]
            if day >= term_day:
                return LunarToEarthlyBranch.EARTHLY_BRANCHES[11]  # 丑月
            else:
                return LunarToEarthlyBranch.EARTHLY_BRANCHES[10]  # 子月
        else:
            term_idx = month - 1
            prev_term = solar_terms[term_idx - 1]
            if day >= prev_term[1]:
                return LunarToEarthlyBranch.EARTHLY_BRANCHES[term_idx - 1]
            else:
                return LunarToEarthlyBranch.EARTHLY_BRANCHES[term_idx - 2]

    @staticmethod
    def get_day_branch(year, month, day):
        """计算日地支（以1900年1月1日庚子日为基准）"""
        base_date = datetime.date(1900, 1, 1)
        target_date = datetime.date(year, month, day)
        delta_days = (target_date - base_date).days
        offset = delta_days % 12
        return LunarToEarthlyBranch.EARTHLY_BRANCHES[offset]

    @staticmethod
    def get_hour_branch(hour):
        """计算时辰地支（2小时为一时辰）"""
        hour_segment = (hour + 1) // 2  # 23-1点为0（子），1-3点为1（丑）...
        return LunarToEarthlyBranch.EARTHLY_BRANCHES[hour_segment % 12]