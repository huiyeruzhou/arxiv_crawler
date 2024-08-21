from bs4 import Tag
from typing_extensions import Literal

CATS_MAP = {
    "astro-ph.CO": {
        "en": "Cosmology and Nongalactic Astrophysics",
        "zh-CN": "宇宙学和非银河系天体物理学",
    },
    "astro-ph.EP": {
        "en": "Earth and Planetary Astrophysics",
        "zh-CN": "地球和行星天体物理学",
    },
    "astro-ph.GA": {"en": "Astrophysics of Galaxies", "zh-CN": "星系天体物理学"},
    "astro-ph.HE": {
        "en": "High Energy Astrophysical Phenomena",
        "zh-CN": "高能天体物理现象",
    },
    "astro-ph.IM": {
        "en": "Instrumentation and Methods for Astrophysics",
        "zh-CN": "天体物理学仪器和方法",
    },
    "astro-ph.SR": {
        "en": "Solar and Stellar Astrophysics",
        "zh-CN": "太阳和恒星天体物理学",
    },
    "cond-mat.dis-nn": {
        "en": "Disordered Systems and Neural Networks",
        "zh-CN": "无序系统和神经网络",
    },
    "cond-mat.mes-hall": {
        "en": "Mesoscale and Nanoscale Physics",
        "zh-CN": "介观和纳米物理",
    },
    "cond-mat.mtrl-sci": {"en": "Materials Science", "zh-CN": "材料科学"},
    "cond-mat.other": {"en": "Other Condensed Matter", "zh-CN": "其他凝聚态物质"},
    "cond-mat.quant-gas": {"en": "Quantum Gases", "zh-CN": "量子气体"},
    "cond-mat.soft": {"en": "Soft Condensed Matter", "zh-CN": "软凝聚态物质"},
    "cond-mat.stat-mech": {"en": "Statistical Mechanics", "zh-CN": "统计力学"},
    "cond-mat.str-el": {"en": "Strongly Correlated Electrons", "zh-CN": "强关联电子"},
    "cond-mat.supr-con": {"en": "Superconductivity", "zh-CN": "超导"},
    "cs.AI": {"en": "Artificial Intelligence", "zh-CN": "人工智能"},
    "cs.AR": {"en": "Hardware Architecture", "zh-CN": "硬件架构"},
    "cs.CC": {"en": "Computational Complexity", "zh-CN": "计算复杂度"},
    "cs.CE": {
        "en": "Computational Engineering, Finance, and Science",
        "zh-CN": "计算工程、金融和科学",
    },
    "cs.CG": {"en": "Computational Geometry", "zh-CN": "计算几何"},
    "cs.CL": {"en": "Computation and Language", "zh-CN": "计算语言学"},
    "cs.CR": {"en": "Cryptography and Security", "zh-CN": "密码学和安全"},
    "cs.CV": {
        "en": "Computer Vision and Pattern Recognition",
        "zh-CN": "计算机视觉和模式识别",
    },
    "cs.CY": {"en": "Computers and Society", "zh-CN": "计算机与社会"},
    "cs.DB": {"en": "Databases", "zh-CN": "数据库"},
    "cs.DC": {
        "en": "Distributed, Parallel, and Cluster Computing",
        "zh-CN": "分布式、并行和集群计算",
    },
    "cs.DL": {"en": "Digital Libraries", "zh-CN": "数字图书馆"},
    "cs.DM": {"en": "Discrete Mathematics", "zh-CN": "离散数学"},
    "cs.DS": {"en": "Data Structures and Algorithms", "zh-CN": "数据结构和算法"},
    "cs.ET": {"en": "Emerging Technologies", "zh-CN": "新兴技术"},
    "cs.FL": {
        "en": "Formal Languages and Automata Theory",
        "zh-CN": "形式语言和自动机理论",
    },
    "cs.GL": {"en": "General Literature", "zh-CN": "一般文献"},
    "cs.GR": {"en": "Graphics", "zh-CN": "图形"},
    "cs.GT": {"en": "Computer Science and Game Theory", "zh-CN": "计算机科学与博弈论"},
    "cs.HC": {"en": "Human-Computer Interaction", "zh-CN": "人机交互"},
    "cs.IR": {"en": "Information Retrieval", "zh-CN": "信息检索"},
    "cs.IT": {"en": "Information Theory", "zh-CN": "信息论"},
    "cs.LG": {"en": "Machine Learning", "zh-CN": "机器学习"},
    "cs.LO": {"en": "Logic in Computer Science", "zh-CN": "计算机科学中的逻辑"},
    "cs.MA": {"en": "Multiagent Systems", "zh-CN": "多代理系统"},
    "cs.MM": {"en": "Multimedia", "zh-CN": "多媒体"},
    "cs.MS": {"en": "Mathematical Software", "zh-CN": "数学软件"},
    "cs.NA": {"en": "Numerical Analysis", "zh-CN": "数值分析"},
    "cs.NE": {"en": "Neural and Evolutionary Computing", "zh-CN": "神经和进化计算"},
    "cs.NI": {
        "en": "Networking and Internet Architecture",
        "zh-CN": "网络和互联网架构",
    },
    "cs.OH": {"en": "Other Computer Science", "zh-CN": "其他计算机科学"},
    "cs.OS": {"en": "Operating Systems", "zh-CN": "操作系统"},
    "cs.PF": {"en": "Performance", "zh-CN": "表现"},
    "cs.PL": {"en": "Programming Languages", "zh-CN": "编程语言"},
    "cs.RO": {"en": "Robotics", "zh-CN": "机器人技术"},
    "cs.SC": {"en": "Symbolic Computation", "zh-CN": "符号计算"},
    "cs.SD": {"en": "Sound", "zh-CN": "声音"},
    "cs.SE": {"en": "Software Engineering", "zh-CN": "软件工程"},
    "cs.SI": {"en": "Social and Information Networks", "zh-CN": "社交和信息网络"},
    "cs.SY": {"en": "Systems and Control", "zh-CN": "系统与控制"},
    "econ.EM": {"en": "Econometrics", "zh-CN": "计量经济学"},
    "econ.GN": {"en": "General Economics", "zh-CN": "普通经济学"},
    "econ.TH": {"en": "Theoretical Economics", "zh-CN": "理论经济学"},
    "eess.AS": {"en": "Audio and Speech Processing", "zh-CN": "音频和语音处理"},
    "eess.IV": {"en": "Image and Video Processing", "zh-CN": "图像和视频处理"},
    "eess.SP": {"en": "Signal Processing", "zh-CN": "信号处理"},
    "eess.SY": {"en": "Systems and Control", "zh-CN": "系统与控制"},
    "gr-qc": {
        "en": "General Relativity and Quantum Cosmology",
        "zh-CN": "广义相对论和量子宇宙学",
    },
    "hep-ex": {"en": "High Energy Physics - Experiment", "zh-CN": "高能物理-实验"},
    "hep-lat": {"en": "High Energy Physics - Lattice", "zh-CN": "高能物理-晶格"},
    "hep-ph": {"en": "High Energy Physics - Phenomenology", "zh-CN": "高能物理-现象学"},
    "hep-th": {"en": "High Energy Physics - Theory", "zh-CN": "高能物理 - 理论"},
    "math-ph": {"en": "Mathematical Physics", "zh-CN": "数学物理"},
    "math.AC": {"en": "Commutative Algebra", "zh-CN": "交换代数"},
    "math.AG": {"en": "Algebraic Geometry", "zh-CN": "代数几何"},
    "math.AP": {"en": "Analysis of PDEs", "zh-CN": "偏微分方程分析"},
    "math.AT": {"en": "Algebraic Topology", "zh-CN": "代数拓扑"},
    "math.CA": {"en": "Classical Analysis and ODEs", "zh-CN": "经典分析和常微分方程"},
    "math.CO": {"en": "Combinatorics", "zh-CN": "组合学"},
    "math.CT": {"en": "Category Theory", "zh-CN": "范畴论"},
    "math.CV": {"en": "Complex Variables", "zh-CN": "复杂变量"},
    "math.DG": {"en": "Differential Geometry", "zh-CN": "微分几何"},
    "math.DS": {"en": "Dynamical Systems", "zh-CN": "动力系统"},
    "math.FA": {"en": "Functional Analysis", "zh-CN": "泛函分析"},
    "math.GM": {"en": "General Mathematics", "zh-CN": "普通数学"},
    "math.GN": {"en": "General Topology", "zh-CN": "通用拓扑"},
    "math.GR": {"en": "Group Theory", "zh-CN": "群论"},
    "math.GT": {"en": "Geometric Topology", "zh-CN": "几何拓扑"},
    "math.HO": {"en": "History and Overview", "zh-CN": "历史与概述"},
    "math.IT": {"en": "Information Theory", "zh-CN": "信息论"},
    "math.KT": {"en": "K-Theory and Homology", "zh-CN": "K-理论和同源性"},
    "math.LO": {"en": "Logic", "zh-CN": "逻辑"},
    "math.MG": {"en": "Metric Geometry", "zh-CN": "公制几何"},
    "math.MP": {"en": "Mathematical Physics", "zh-CN": "数学物理"},
    "math.NA": {"en": "Numerical Analysis", "zh-CN": "数值分析"},
    "math.NT": {"en": "Number Theory", "zh-CN": "数论"},
    "math.OA": {"en": "Operator Algebras", "zh-CN": "算子代数"},
    "math.OC": {"en": "Optimization and Control", "zh-CN": "优化与控制"},
    "math.PR": {"en": "Probability", "zh-CN": "可能性"},
    "math.QA": {"en": "Quantum Algebra", "zh-CN": "量子代数"},
    "math.RA": {"en": "Rings and Algebras", "zh-CN": "环和代数"},
    "math.RT": {"en": "Representation Theory", "zh-CN": "表征论"},
    "math.SG": {"en": "Symplectic Geometry", "zh-CN": "辛几何"},
    "math.SP": {"en": "Spectral Theory", "zh-CN": "谱理论"},
    "math.ST": {"en": "Statistics Theory", "zh-CN": "统计理论"},
    "nlin.AO": {
        "en": "Adaptation and Self-Organizing Systems",
        "zh-CN": "适应和自组织系统",
    },
    "nlin.CD": {"en": "Chaotic Dynamics", "zh-CN": "混沌动力学"},
    "nlin.CG": {
        "en": "Cellular Automata and Lattice Gases",
        "zh-CN": "元胞自动机和晶格气体",
    },
    "nlin.PS": {"en": "Pattern Formation and Solitons", "zh-CN": "模式形成和孤子"},
    "nlin.SI": {
        "en": "Exactly Solvable and Integrable Systems",
        "zh-CN": "精确可解可积系统",
    },
    "nucl-ex": {"en": "Nuclear Experiment", "zh-CN": "核实验"},
    "nucl-th": {"en": "Nuclear Theory", "zh-CN": "核理论"},
    "physics.acc-ph": {"en": "Accelerator Physics", "zh-CN": "加速器物理"},
    "physics.ao-ph": {
        "en": "Atmospheric and Oceanic Physics",
        "zh-CN": "大气和海洋物理",
    },
    "physics.app-ph": {"en": "Applied Physics", "zh-CN": "应用物理"},
    "physics.atm-clus": {
        "en": "Atomic and Molecular Clusters",
        "zh-CN": "原子和分子簇",
    },
    "physics.atom-ph": {"en": "Atomic Physics", "zh-CN": "原子物理学"},
    "physics.bio-ph": {"en": "Biological Physics", "zh-CN": "生物物理学"},
    "physics.chem-ph": {"en": "Chemical Physics", "zh-CN": "化学物理"},
    "physics.class-ph": {"en": "Classical Physics", "zh-CN": "经典物理学"},
    "physics.comp-ph": {"en": "Computational Physics", "zh-CN": "计算物理"},
    "physics.data-an": {
        "en": "Data Analysis, Statistics and Probability",
        "zh-CN": "数据分析、统计和概率",
    },
    "physics.ed-ph": {"en": "Physics Education", "zh-CN": "物理教育"},
    "physics.flu-dyn": {"en": "Fluid Dynamics", "zh-CN": "流体动力学"},
    "physics.gen-ph": {"en": "General Physics", "zh-CN": "普通物理"},
    "physics.geo-ph": {"en": "Geophysics", "zh-CN": "地球物理学"},
    "physics.hist-ph": {
        "en": "History and Philosophy of Physics",
        "zh-CN": "物理学史与哲学",
    },
    "physics.ins-det": {
        "en": "Instrumentation and Detectors",
        "zh-CN": "仪器仪表和探测器",
    },
    "physics.med-ph": {"en": "Medical Physics", "zh-CN": "医学物理"},
    "physics.optics": {"en": "Optics", "zh-CN": "光学"},
    "physics.plasm-ph": {"en": "Plasma Physics", "zh-CN": "等离子体物理"},
    "physics.pop-ph": {"en": "Popular Physics", "zh-CN": "大众物理"},
    "physics.soc-ph": {"en": "Physics and Society", "zh-CN": "物理与社会"},
    "physics.space-ph": {"en": "Space Physics", "zh-CN": "空间物理学"},
    "q-bio.BM": {"en": "Biomolecules", "zh-CN": "生物分子"},
    "q-bio.CB": {"en": "Cell Behavior", "zh-CN": "细胞行为"},
    "q-bio.GN": {"en": "Genomics", "zh-CN": "基因组学"},
    "q-bio.MN": {"en": "Molecular Networks", "zh-CN": "分子网络"},
    "q-bio.NC": {"en": "Neurons and Cognition", "zh-CN": "神经元和认知"},
    "q-bio.OT": {"en": "Other Quantitative Biology", "zh-CN": "其他定量生物学"},
    "q-bio.PE": {"en": "Populations and Evolution", "zh-CN": "种群与进化"},
    "q-bio.QM": {"en": "Quantitative Methods", "zh-CN": "定量方法"},
    "q-bio.SC": {"en": "Subcellular Processes", "zh-CN": "亚细胞过程"},
    "q-bio.TO": {"en": "Tissues and Organs", "zh-CN": "组织和器官"},
    "q-fin.CP": {"en": "Computational Finance", "zh-CN": "计算金融"},
    "q-fin.EC": {"en": "Economics", "zh-CN": "经济学"},
    "q-fin.GN": {"en": "General Finance", "zh-CN": "一般财务"},
    "q-fin.MF": {"en": "Mathematical Finance", "zh-CN": "数学金融"},
    "q-fin.PM": {"en": "Portfolio Management", "zh-CN": "投资组合管理"},
    "q-fin.PR": {"en": "Pricing of Securities", "zh-CN": "证券定价"},
    "q-fin.RM": {"en": "Risk Management", "zh-CN": "风险管理"},
    "q-fin.ST": {"en": "Statistical Finance", "zh-CN": "统计金融"},
    "q-fin.TR": {
        "en": "Trading and Market Microstructure",
        "zh-CN": "交易和市场微观结构",
    },
    "quant-ph": {"en": "Quantum Physics", "zh-CN": "量子物理学"},
    "stat.AP": {"en": "Applications", "zh-CN": "应用领域"},
    "stat.CO": {"en": "Computation", "zh-CN": "计算"},
    "stat.ME": {"en": "Methodology", "zh-CN": "方法论"},
    "stat.ML": {"en": "Machine Learning", "zh-CN": "机器学习"},
    "stat.OT": {"en": "Other Statistics", "zh-CN": "其他统计数据"},
    "stat.TH": {"en": "Statistics Theory", "zh-CN": "统计理论"},
}


def parse_categories(categories, lang: Literal["zh-CN", "en"] = "zh-CN"):
    """
    将arxiv的分类转换为对应语言的版本。
    如果没有对应的语言版本抛出KeyError,如果分类不在CATS_MAP中,抛出KeyError

    Args:
        categories (list): 分类列表
        lang (str, optional): 目标语言. Defaults to "zh-CN".
    """
    return [CATS_MAP[category][lang] for category in categories]


if __name__ == "__main__":
    # 运行下面这段代码，可以获取CATS_MAP
    import requests
    from bs4 import BeautifulSoup

    from async_translator import translate

    # 请求页面内容
    url = "https://arxiv.org/category_taxonomy"
    response = requests.get(url)

    # 检查请求是否成功
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        domains = {}

        # 选择所有目标 <div> 元素
        divs = soup.select("div.column.is-one-fifth h4")
        """形如:
        <div class="column is-one-fifth">
            <h4>cs.AI <span>(Artificial Intelligence)</span></h4>
        </div>
        """

        for div in divs:
            # 获取 h4 标签中的直接文本 (即 cs.AI 部分)
            category_code = div.contents[0].strip()

            # 获取 <span> 标签中的文本 (即 Artificial Intelligence 部分)
            english_name_tag = div.find("span")
            assert isinstance(english_name_tag, Tag)
            english_name = english_name_tag.get_text(strip=True)

            # 构造字典条目
            domains[category_code] = {
                "en": english_name,
                "zh-CN": translate(english_name, langto="zh-CN"),
            }

        # 输出结果
        import pprint

        # 机翻结果修正
        domains["cs.GL"]["zh-CN"] = "一般文献"
        domains["cs.CL"]["zh-CN"] = "计算语言学"
        pprint.pprint(domains)
    else:
        print(f"Failed to retrieve webpage, status code: {response.status_code}")
