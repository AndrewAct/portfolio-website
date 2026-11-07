"""Bilingual editorial material, not claims about a reader or astrological predictions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Scene:
    zh: str
    en: str


@dataclass(frozen=True)
class FocusArea:
    key: str
    zh: str
    en: str
    scenes: tuple[Scene, ...]


# Scene pairs refer to the same situation in either language. Only one reaches the prompt.
FOCUS_AREAS = (
    FocusArea(
        "sleep",
        "睡眠与作息",
        "sleep and daily rhythms",
        (
            Scene("睡前还想给自己留一点自由时间", "wanting a little time to yourself before bed"),
            Scene("早起之后，怎样不急着进入忙碌", "easing into the day after waking early"),
            Scene(
                "午后犯困时，给日程留一个短暂停顿",
                "making room for a short pause during an afternoon slump",
            ),
            Scene(
                "周末和工作日之间，找到舒服的作息节奏",
                "finding a comfortable rhythm between weekends and weekdays",
            ),
        ),
    ),
    FocusArea(
        "body",
        "身体与舒适感",
        "physical comfort",
        (
            Scene(
                "专注一阵之后，起身舒展一下",
                "getting up to stretch after a stretch of concentration",
            ),
            Scene(
                "在电梯和楼梯之间，选一点不勉强的活动",
                "choosing a little easy movement on an everyday errand",
            ),
            Scene(
                "调整座椅或屏幕，让常待的位置舒服一点",
                "adjusting a chair or screen to make a familiar spot comfortable",
            ),
            Scene(
                "发现衣服或鞋子不舒服，优先照顾自己的感受",
                "putting comfort first when clothes or shoes feel awkward",
            ),
        ),
    ),
    FocusArea(
        "eating",
        "饮食",
        "food and meals",
        (
            Scene(
                "在忙碌中，认真选一顿自己想吃的饭",
                "choosing a meal you actually want during a busy day",
            ),
            Scene(
                "对熟悉的做法换一种调味，看看是否合口味",
                "trying a different seasoning in a familiar dish",
            ),
            Scene(
                "和别人点餐时，说出自己真正想吃什么",
                "saying what you actually fancy when ordering with others",
            ),
            Scene(
                "一个人吃饭，也把这段时间过得自在一点",
                "making a meal alone feel comfortable and unhurried",
            ),
        ),
    ),
    FocusArea(
        "partner",
        "亲近与相处",
        "closeness and affection",
        (
            Scene(
                "想表达关心，又不想显得太郑重",
                "wanting to show care without making a grand gesture",
            ),
            Scene(
                "一次低压力的邀约，给彼此留出选择",
                "making a low-pressure invitation with room for either answer",
            ),
            Scene(
                "亲近的人各自忙碌，商量适合彼此的相处方式",
                "finding a comfortable way to connect when both people are busy",
            ),
            Scene(
                "有人记得一个小偏好时，愿意接住这份心意",
                "receiving a thoughtful gesture about a small preference",
            ),
        ),
    ),
    FocusArea(
        "family",
        "家人与牵挂",
        "family and familiar ties",
        (
            Scene(
                "向家人分享一件不需要很隆重的小近况", "sharing a small, ordinary update with family"
            ),
            Scene(
                "听到熟悉的叮嘱，选择自己舒服的回应方式",
                "finding a comfortable response to familiar family advice",
            ),
            Scene(
                "不一定长聊，用一次简单问候保持联系",
                "staying in touch with a short check-in rather than a long call",
            ),
            Scene(
                "一起安排一件家里的小事，听听各自的偏好",
                "hearing everyone's preferences for a small family arrangement",
            ),
        ),
    ),
    FocusArea(
        "friends",
        "朋友",
        "friendship",
        (
            Scene(
                "看到有趣的东西，想起一个会懂的朋友",
                "spotting something funny that a particular friend would appreciate",
            ),
            Scene(
                "朋友的邀约和自己的空闲，怎么安排更轻松",
                "finding an easy fit between an invitation and your free time",
            ),
            Scene(
                "聊天不一定有结论，互相接几句话也很愉快",
                "enjoying a conversation that does not need to reach a conclusion",
            ),
            Scene(
                "重新联系一位有阵子没聊的朋友，不必铺垫太多",
                "reconnecting with a friend without an elaborate explanation",
            ),
        ),
    ),
    FocusArea(
        "coworkers",
        "合作与搭把手",
        "cooperation and shared effort",
        (
            Scene(
                "一起做事前，先说清各自负责哪一小部分",
                "clarifying who handles which small part of a shared task",
            ),
            Scene(
                "对方的做法不同，先了解思路再决定怎么配合",
                "understanding a different approach before deciding how to cooperate",
            ),
            Scene(
                "有人愿意帮忙时，把任务交代清楚就够了",
                "giving clear context when someone offers to help",
            ),
            Scene(
                "及时告诉一起做事的人，哪个细节帮到了自己",
                "telling a collaborator which small contribution helped",
            ),
        ),
    ),
    FocusArea(
        "authority",
        "反馈与表达",
        "feedback and expression",
        (
            Scene(
                "说明一个想法时，先讲最想让人理解的那一点",
                "starting an explanation with the one point that matters most",
            ),
            Scene(
                "收到建议后，分清哪些值得采用、哪些可以放下",
                "sorting useful feedback from suggestions you can leave aside",
            ),
            Scene(
                "展示还不完美的进度，听一听不同看法",
                "sharing unfinished progress to hear another perspective",
            ),
            Scene(
                "表达不同意见时，找一种清楚又不紧绷的说法",
                "expressing a different opinion clearly without making it tense",
            ),
        ),
    ),
    FocusArea(
        "money",
        "钱与取舍",
        "money and everyday value",
        (
            Scene(
                "一件想买的小东西，是喜欢还是只是顺手",
                "deciding whether a small purchase is wanted or merely convenient",
            ),
            Scene(
                "一次大家分摊的小开销，提前讲清更省心",
                "clearing up a small shared expense before it becomes awkward",
            ),
            Scene(
                "翻看自动续费项目，留下真正用得上的",
                "keeping only the subscriptions that actually earn their place",
            ),
            Scene(
                "在便宜一点和省事一点之间，按自己的需要取舍",
                "weighing a lower price against convenience for your own needs",
            ),
        ),
    ),
    FocusArea(
        "postponed",
        "待办与小决定",
        "pending tasks and small decisions",
        (
            Scene(
                "一封不需要完美措辞的简单回复", "a simple reply that does not need perfect wording"
            ),
            Scene(
                "一个迟迟没约的时间，先确认自己方便的范围",
                "checking your availability before setting a pending appointment",
            ),
            Scene(
                "把一件看着很大的待办，拆出最容易开始的部分",
                "finding the easiest first piece of an intimidating task",
            ),
            Scene(
                "决定一件小事还要不要做，也可以直接取消",
                "deciding whether a lingering task still deserves to be done",
            ),
        ),
    ),
    FocusArea(
        "past",
        "旧人旧事",
        "memories and familiar things",
        (
            Scene(
                "熟悉的旋律勾起回忆，停一会儿也没关系",
                "letting a familiar tune bring back a memory without rushing on",
            ),
            Scene(
                "整理旧照片时，留意自己现在喜欢怎样的生活",
                "noticing your present preferences while looking through old photos",
            ),
            Scene(
                "偶然想到一个旧爱好，试试是否还喜欢",
                "trying an old hobby again to see whether it still feels enjoyable",
            ),
            Scene(
                "一件有回忆的小物，是留下还是换种方式保存",
                "deciding how to keep a small keepsake or its memory",
            ),
        ),
    ),
    FocusArea(
        "self_talk",
        "自我期待",
        "personal expectations",
        (
            Scene(
                "看见别人的进展时，也承认自己的步调",
                "recognizing your own pace when noticing someone else's progress",
            ),
            Scene(
                "一件事做到够用就停，不继续打磨无关细节",
                "stopping when a task works instead of polishing minor details",
            ),
            Scene(
                "注意到一个小进步，不急着立刻提高标准",
                "noticing small progress before raising the bar again",
            ),
            Scene(
                "给今天设一个适合实际精力的目标",
                "setting a goal that fits the capacity you actually have today",
            ),
        ),
    ),
    FocusArea(
        "boundaries",
        "偏好与边界",
        "preferences and boundaries",
        (
            Scene(
                "收到一个请求，先看看自己是否有余力",
                "checking your capacity before agreeing to a request",
            ),
            Scene(
                "想独处时，简单说清自己的安排",
                "explaining your plans simply when you want time alone",
            ),
            Scene(
                "大家意见不同时，也说出一个自己的偏好",
                "voicing a preference when the group wants different things",
            ),
            Scene(
                "回复消息的节奏，可以商量而不必一直在线",
                "finding a comfortable messaging rhythm without staying constantly online",
            ),
        ),
    ),
    FocusArea(
        "overload",
        "精力与安排",
        "time and capacity",
        (
            Scene(
                "几件事碰到一起，先选真正值得优先的那件",
                "choosing what actually deserves priority when tasks pile up",
            ),
            Scene(
                "日程之间留一点余地，不把空白都填满",
                "leaving a little room between plans instead of filling every gap",
            ),
            Scene(
                "一件琐事是否可以交给别人，自己只负责说明",
                "handing over a small task with enough explanation to let it go",
            ),
            Scene(
                "兴致很高时，也给后半天留一点体力",
                "saving some capacity for later even when enthusiasm is high",
            ),
        ),
    ),
    FocusArea(
        "learning",
        "学习与好奇心",
        "learning and curiosity",
        (
            Scene(
                "遇到不懂的小问题，顺手查清而不要求学完全部",
                "looking up one small question without mastering the whole subject",
            ),
            Scene(
                "换一种解释或练习方式，看看是否更好懂",
                "trying another explanation or exercise to make something click",
            ),
            Scene(
                "向别人请教一个具体问题，省去独自绕弯",
                "asking one precise question instead of puzzling alone",
            ),
            Scene(
                "把刚学到的小知识，用在一件实际的小事上",
                "using something newly learned in a small practical way",
            ),
        ),
    ),
    FocusArea(
        "hobbies",
        "兴趣与手艺",
        "hobbies and making things",
        (
            Scene(
                "做一点只为好玩的手工，不急着展示成果",
                "making something for fun without preparing it for an audience",
            ),
            Scene(
                "为旧兴趣留十分钟，看看手感是否还在",
                "giving an old interest ten minutes to see how it feels",
            ),
            Scene(
                "用现有的材料试试新做法，不用先买齐装备",
                "trying a new technique with what is already at hand",
            ),
            Scene(
                "允许一件小作品保留一点不规整的个人趣味",
                "letting a small creation keep its imperfect personal character",
            ),
        ),
    ),
    FocusArea(
        "home",
        "居家与小整理",
        "home and everyday spaces",
        (
            Scene(
                "挪动一件常用物品，让拿取顺手一点",
                "moving an everyday item so it is easier to reach",
            ),
            Scene(
                "只收拾一个小角落，不把整理变成大工程",
                "tidying one small corner without starting a major project",
            ),
            Scene(
                "和同住的人商量一个让彼此方便的小安排",
                "agreeing on a small household arrangement that works for everyone",
            ),
            Scene(
                "留出一处可以随手坐下休息的位置",
                "making space for a spot where you can sit and pause",
            ),
        ),
    ),
    FocusArea(
        "outdoors",
        "户外与附近",
        "outdoors and nearby places",
        (
            Scene(
                "在附近走一小段，留意一处平常忽略的变化",
                "taking a short local walk and noticing a small change",
            ),
            Scene(
                "有一点空闲，选一处不用费心规划的户外地点",
                "choosing an easy outdoor spot for a little free time",
            ),
            Scene(
                "按天气和自己的状态，调整出门的距离",
                "adjusting the length of an outing to the weather and your mood",
            ),
            Scene(
                "经过熟悉的路口，看看另一条路有什么不同",
                "trying a different turn on a familiar route",
            ),
        ),
    ),
    FocusArea(
        "play",
        "玩心与轻松",
        "play and lightheartedness",
        (
            Scene(
                "给普通的小事加一点好玩的规则",
                "adding a playful little rule to an ordinary activity",
            ),
            Scene(
                "和熟悉的人开个双方都舒服的小玩笑",
                "sharing an easy joke that both people can enjoy",
            ),
            Scene(
                "玩一局不计较输赢的小游戏",
                "enjoying a short game without keeping score too seriously",
            ),
            Scene(
                "做一个不需要用途、只是有趣的小尝试", "trying something simply because it seems fun"
            ),
        ),
    ),
    FocusArea(
        "solitude",
        "独处与自在",
        "solitude and ease",
        (
            Scene(
                "空下来的半小时，可以不急着安排内容",
                "letting an unexpected half-hour stay unplanned",
            ),
            Scene(
                "一个人去熟悉的地方，不必等大家都有空",
                "visiting a familiar place without waiting for company",
            ),
            Scene(
                "独处时，按自己的喜好选择声音或安静",
                "choosing sound or quiet to suit your own company",
            ),
            Scene(
                "有人取消安排，看看自己想怎样用这段时间",
                "choosing what you want from time freed by a canceled plan",
            ),
        ),
    ),
    FocusArea(
        "messages",
        "消息与沟通",
        "messages and everyday communication",
        (
            Scene(
                "文字容易显得生硬时，补一句简单的说明",
                "adding a little context when a short message could sound abrupt",
            ),
            Scene(
                "群聊里只回应真正想参与的那一小段",
                "joining just the part of a group chat that interests you",
            ),
            Scene(
                "收到一条不确定意思的回复，先问清而不猜测",
                "clarifying an ambiguous reply instead of guessing its meaning",
            ),
            Scene(
                "想说的话很多，先把最重要的一句说清楚",
                "leading with the one sentence that matters in a longer message",
            ),
        ),
    ),
    FocusArea(
        "plans",
        "计划与变通",
        "plans and flexibility",
        (
            Scene(
                "原定安排有小变化，挑一个省力的替代方案",
                "finding an easy alternative when a plan changes slightly",
            ),
            Scene(
                "留一个备用时间，免得为小延误来回赶",
                "leaving a spare time slot for ordinary delays",
            ),
            Scene(
                "有几个都不错的选项，按今天的状态来选",
                "choosing between good options based on today's mood",
            ),
            Scene(
                "别人临时起意时，也可以按自己的节奏决定",
                "taking your time with someone else's spontaneous suggestion",
            ),
        ),
    ),
    FocusArea(
        "attention",
        "专注与信息",
        "attention and information",
        (
            Scene(
                "正想认真做一件事，先减少一种不必要的打扰",
                "removing one unnecessary interruption before focusing",
            ),
            Scene(
                "看了很多信息后，留意哪一条真正用得上",
                "picking out the one useful detail after browsing a lot of information",
            ),
            Scene(
                "一件事做到一半，先记下别的念头再继续",
                "jotting down a distracting idea before returning to the task",
            ),
            Scene(
                "不急着收藏更多内容，先试用一个已有的建议",
                "trying one saved idea before collecting more advice",
            ),
        ),
    ),
    FocusArea(
        "music",
        "音乐与阅读",
        "music and reading",
        (
            Scene(
                "重听一首熟悉的歌，留意以前没注意的部分", "noticing a new detail in a familiar song"
            ),
            Scene(
                "读几页喜欢的书，不把阅读变成打卡",
                "reading a few enjoyable pages without a completion target",
            ),
            Scene(
                "凭自己的兴趣选一部作品，不追着热门走",
                "choosing something to read or hear based on your own taste",
            ),
            Scene(
                "把一句有意思的话分享给愿意聊的人",
                "sharing an interesting line with someone who might enjoy discussing it",
            ),
        ),
    ),
    FocusArea(
        "errands",
        "出行与小差事",
        "getting around and errands",
        (
            Scene(
                "把顺路的两件小事一起办，给自己省一趟",
                "combining two nearby errands to save an extra trip",
            ),
            Scene(
                "等待的空档，不一定要拿来处理更多事情",
                "letting a wait be a pause rather than another productivity slot",
            ),
            Scene(
                "出门前确认一个小细节，路上会更从容", "checking one small detail before heading out"
            ),
            Scene(
                "一条熟悉的路线，也可以选更合心情的走法",
                "choosing a version of a familiar route that suits your mood",
            ),
        ),
    ),
    FocusArea(
        "community",
        "邻里与善意",
        "community and small kindnesses",
        (
            Scene(
                "遇到常见面的人，用一次自然的招呼回应",
                "offering a natural greeting to a familiar face",
            ),
            Scene(
                "有人顺手帮忙，简单认真地道个谢",
                "giving a sincere, simple thanks for a small favor",
            ),
            Scene(
                "分享一条对别人有用的本地小消息",
                "sharing a small piece of useful local information",
            ),
            Scene(
                "一件力所能及的小事，按舒服的分寸伸手",
                "offering a little help that fits comfortably within your capacity",
            ),
        ),
    ),
    FocusArea(
        "taste",
        "穿搭与审美",
        "personal style and taste",
        (
            Scene(
                "从已有的衣物里搭出一点今天想要的感觉",
                "putting together familiar clothes to suit today's mood",
            ),
            Scene(
                "在流行和自己的喜好之间，更信任实际感受",
                "weighing a trend against what you actually enjoy",
            ),
            Scene(
                "换一个小配件，看看熟悉的东西是否变有趣",
                "trying a small accessory with something familiar",
            ),
            Scene(
                "整理常用的小物，留下看着和用着都顺心的",
                "keeping everyday objects that feel good to use and look at",
            ),
        ),
    ),
    FocusArea(
        "small_wins",
        "完成与小进展",
        "finishing things and small wins",
        (
            Scene(
                "给一件已完成的小事收个尾，不急着接下一件",
                "closing out a finished task before rushing into the next",
            ),
            Scene(
                "留意一件已经比上次顺手的事情",
                "noticing something that feels easier than it did last time",
            ),
            Scene("把一个想法变成能看见的小成果", "turning an idea into one small visible result"),
            Scene(
                "一天不必做很多，有一件推进一点就很好",
                "letting modest progress on one thing count for the day",
            ),
        ),
    ),
)


@dataclass(frozen=True)
class ReadingApproach:
    key: str
    zh: str
    en: str


# Directions, not sample sentences: quoted examples previously leaked into the output.
READING_APPROACHES = (
    ReadingApproach(
        "mixed_feelings",
        "理解同一件小事里两种都说得通的心情",
        "explore two understandable feelings about one small situation",
    ),
    ReadingApproach(
        "small_pleasure", "留意一处容易被忽略的小乐趣", "notice an easily missed small pleasure"
    ),
    ReadingApproach(
        "gentle_caution",
        "体谅一个可能的小麻烦，给出轻松的应对方式",
        "consider a possible small snag with an easy way to handle it",
    ),
    ReadingApproach(
        "small_choice",
        "理解一个日常选择里的犹豫，留给读者决定",
        "respect hesitation around an everyday choice and leave the decision open",
    ),
    ReadingApproach(
        "fresh_perspective",
        "换个看法，写出哪里可以省力或有趣一点",
        "offer a fresh view of what could make this easier or more enjoyable",
    ),
    ReadingApproach(
        "curiosity",
        "带一点好奇心，试一个不费力也不必坚持的新做法",
        "explore an easy experiment with no obligation to keep doing it",
    ),
    ReadingApproach(
        "small_progress",
        "注意一个细微的变化，不急着把它夸成大成就",
        "notice a modest change without inflating it into an achievement",
    ),
    ReadingApproach(
        "room_to_breathe",
        "给这件事留一点弹性，不必安排得太满",
        "leave some flexibility instead of planning every detail",
    ),
    ReadingApproach(
        "personal_taste",
        "分清自己喜欢什么，不追求一个标准答案",
        "consider a personal preference without seeking a correct answer",
    ),
    ReadingApproach(
        "small_discovery",
        "从一个细节里发现和平常不太一样的地方",
        "find a small detail that feels different from the usual",
    ),
    ReadingApproach(
        "light_humor",
        "轻轻写出一点日常趣味，不拿读者开涮",
        "find gentle everyday humor without making the reader the joke",
    ),
    ReadingApproach(
        "revisit",
        "重新试试一种熟悉的做法，看它是否仍适合现在",
        "revisit something familiar and consider whether it still suits the present",
    ),
)


@dataclass(frozen=True)
class SignProfile:
    preferred_topics: tuple[str, ...]
    zh: str
    en: str


# Same order as ZODIAC_EN. Editorial preferences, not empirical personality claims.
# Preferred topics receive weight 2; every other topic keeps weight 1.
SIGN_PROFILES = (
    SignProfile(
        ("outdoors", "play", "small_wins", "body", "plans", "hobbies"),
        "可偏向直接、愿意试一试的表达，也给犹豫和休息留位置",
        "favor directness and trying things, with room for hesitation and rest",
    ),
    SignProfile(
        ("eating", "home", "money", "taste", "sleep", "music"),
        "可多留意实在的感受和自己的步调，不写成固执或只爱享受",
        "notice tangible comforts and an individual pace without stereotyping stubbornness",
    ),
    SignProfile(
        ("messages", "learning", "friends", "play", "music", "plans"),
        "可偏向好奇、交流和轻巧转念，不写成善变或注意力差",
        "favor curiosity, conversation and flexible thinking without labeling inconsistency",
    ),
    SignProfile(
        ("family", "home", "partner", "past", "eating", "boundaries"),
        "可留意熟悉感和相处细节，也尊重独立与距离",
        "notice familiarity and care while respecting independence and distance",
    ),
    SignProfile(
        ("hobbies", "taste", "friends", "authority", "play", "small_wins"),
        "可留意表达自己的乐趣和被回应的感受，不写成爱出风头",
        "notice self-expression and being heard without assuming a need for attention",
    ),
    SignProfile(
        ("home", "learning", "attention", "errands", "body", "small_wins"),
        "可欣赏顺手的细节与实际改进，不把读者写成挑剔或完美主义",
        "appreciate useful details and practical improvements without assuming perfectionism",
    ),
    SignProfile(
        ("friends", "partner", "taste", "coworkers", "messages", "plans"),
        "可留意双方舒服的分寸，也让自己的偏好有位置",
        "notice mutual ease while making room for the reader's own preferences",
    ),
    SignProfile(
        ("solitude", "partner", "past", "boundaries", "attention", "hobbies"),
        "可留意认真投入和私人空间，不猜测隐情或怀疑别人的动机",
        "notice depth of interest and private space without inventing hidden motives",
    ),
    SignProfile(
        ("outdoors", "learning", "plans", "play", "friends", "errands"),
        "可偏向探索和开阔一点的选择，也允许熟悉和安稳",
        "favor exploration and open choices while allowing familiarity and steadiness",
    ),
    SignProfile(
        ("small_wins", "money", "overload", "postponed", "authority", "self_talk"),
        "可留意可靠的小进展，也写下做得够了就停的余地",
        "notice dependable small progress with room to stop when enough is done",
    ),
    SignProfile(
        ("learning", "community", "hobbies", "messages", "attention", "plans"),
        "可留意不同的做法和有意思的交流，不刻意标榜与众不同",
        "notice alternative approaches and interesting exchanges without forcing uniqueness",
    ),
    SignProfile(
        ("music", "hobbies", "solitude", "partner", "past", "community"),
        "可留意感受和细小联想，但保持具体，不堆砌梦幻意象",
        "notice feelings and small associations while staying concrete rather than dreamy",
    ),
)


# Avoid complete stock expressions rather than banning ordinary words like "creative"
# or "energy", which also have useful literal meanings in these topics.
BANNED_PHRASES_ZH = (
    "闪耀光芒",
    "大放异彩",
    "创造力爆棚",
    "灵感爆棚",
    "能量满满",
    "正能量满满",
    "宇宙的安排",
    "宇宙在提醒你",
    "星象预示",
    "星星为你指路",
    "好运降临",
    "好运爆棚",
    "新的开始",
    "相信你的直觉",
    "跟随内心",
    "机遇与挑战",
    "迎接挑战",
    "勇敢绽放",
    "美好的一天",
    "一切都会好",
    "一切都是最好的安排",
    "成为更好的自己",
    "做最好的自己",
    "你值得被温柔以待",
    "允许自己慢下来",
    "给自己一个拥抱",
    "生活总会给你惊喜",
    "你就是这种人",
    "你向来如此",
    "你心里其实很清楚",
    "只要你愿意迈出第一步",
    "打开新的篇章",
    "拥抱无限可能",
    "幸运女神眷顾",
    "命中注定",
    "注定不平凡",
)
BANNED_PHRASES_EN = (
    "your creativity will shine",
    "let your creativity shine",
    "creative energy is at its peak",
    "shine bright",
    "radiate positivity",
    "positive energy surrounds you",
    "the universe has a plan",
    "the universe is reminding you",
    "the stars are aligned",
    "written in the stars",
    "good fortune awaits",
    "luck is on your side",
    "a new beginning",
    "new beginnings",
    "trust your intuition",
    "follow your heart",
    "opportunities and challenges",
    "embrace the unknown",
    "embrace the journey",
    "unlock your potential",
    "endless possibilities",
    "your best self",
    "the best version of yourself",
    "everything happens for a reason",
    "everything will fall into place",
    "step outside your comfort zone",
    "today is your day",
    "make the most of every moment",
    "give yourself permission",
    "you deserve to be happy",
    "deep down you already know",
    "you are the kind of person who",
    "open a new chapter",
    "destined for greatness",
    "a gentle reminder to",
    "a quiet reminder that",
)
