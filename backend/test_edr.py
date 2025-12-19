"""
EDR 模块测试脚本

用于测试各个组件是否正常工作
"""
import asyncio
import os
import sys

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ 已加载 .env 文件")
except ImportError:
    print("⚠️  python-dotenv 未安装，将只使用系统环境变量")


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


async def test_deepseek_client():
    """测试 DeepSeek API 客户端"""
    print_section("测试 DeepSeek API")
    
    from app.engines.edr.llm_client import DeepSeekClient
    
    client = DeepSeekClient()
    
    if not client.api_key:
        print("❌ DEEPSEEK_API_KEY 未设置")
        print("   请设置环境变量: set DEEPSEEK_API_KEY=你的密钥")
        return False
    
    print(f"✓ API Key 已配置 (前8位: {client.api_key[:8]}...)")
    
    # 测试简单调用
    print("\n测试 API 调用...")
    result = await client.analyze(
        prompt="请用一句话介绍华为公司",
        system_prompt="你是一个企业分析助手"
    )
    
    if result and len(result) > 0:
        print(f"✓ API 调用成功!")
        print(f"   响应: {result[:100]}...")
        return True
    else:
        print("❌ API 调用失败，无响应")
        return False


async def test_tavily_client():
    """测试 Tavily 搜索客户端"""
    print_section("测试 Tavily 搜索 API")
    
    from app.engines.edr.search import TavilySearchClient
    
    client = TavilySearchClient()
    
    if not client.api_key:
        print("❌ TAVILY_API_KEY 未设置")
        print("   请设置环境变量: set TAVILY_API_KEY=你的密钥")
        return False
    
    print(f"✓ API Key 已配置 (前8位: {client.api_key[:8]}...)")
    
    # 测试搜索
    print("\n测试搜索 '华为公司'...")
    result = await client.search("华为公司 简介", max_results=2)
    
    if "error" in result and result["error"]:
        print(f"❌ 搜索失败: {result['error']}")
        return False
    
    results = result.get("results", [])
    print(f"✓ 搜索成功! 找到 {len(results)} 条结果")
    
    for i, r in enumerate(results[:2], 1):
        print(f"\n   结果 {i}:")
        print(f"   标题: {r.get('title', 'N/A')[:50]}")
        print(f"   链接: {r.get('url', 'N/A')[:60]}")
    
    return len(results) > 0


async def test_full_analysis():
    """测试完整分析流程"""
    print_section("测试完整分析流程")
    
    from app.engines.edr import EDRLiteEngine
    
    engine = EDRLiteEngine()
    
    print("开始分析 '腾讯' (这可能需要30-60秒)...\n")
    
    def progress_callback(stage, progress):
        print(f"  [{progress:3d}%] {stage}")
    
    result = await engine.analyze_company(
        company_name="腾讯",
        include_reputation=True,
        progress_callback=progress_callback
    )
    
    if result.get("success"):
        print(f"\n✓ 分析完成!")
        print(f"   公司: {result.get('company_name')}")
        print(f"   评分: {result.get('score')}")
        print(f"   风险等级: {result.get('risk_level')}")
        print(f"   信息源数量: {result.get('sources', {})}")
        print(f"\n   分析摘要 (前500字):")
        print(f"   {result.get('analysis', '')[:500]}...")
        return True
    else:
        print(f"❌ 分析失败: {result.get('error')}")
        return False


async def test_mock_analysis():
    """使用模拟数据测试（不需要 API）"""
    print_section("测试模拟分析（无需 API）")
    
    # 模拟搜索结果
    mock_company_info = {
        "results": [
            {
                "title": "腾讯控股有限公司 - 企业信息",
                "url": "https://example.com/tencent",
                "content": "腾讯控股有限公司成立于1998年，总部位于深圳。是中国最大的互联网公司之一，业务涵盖社交、游戏、金融科技等领域。"
            }
        ]
    }
    
    mock_news_info = {
        "results": [
            {
                "title": "腾讯2024年Q3财报发布",
                "url": "https://example.com/news1",
                "content": "腾讯发布2024年第三季度财报，营收同比增长8%，游戏业务表现强劲。"
            }
        ]
    }
    
    from app.engines.edr.analyzer import RiskAnalyzer
    from app.engines.edr.llm_client import DeepSeekClient
    
    client = DeepSeekClient()
    if not client.api_key:
        print("⚠️  DeepSeek API 未配置，跳过分析测试")
        print("   使用模拟数据展示流程...")
        
        # 显示模拟结果
        print("\n模拟分析结果:")
        print("   公司: 腾讯")
        print("   评分: 75")
        print("   风险等级: 中等风险")
        print("\n   这是模拟数据，配置 API 密钥后可获取真实分析。")
        return True
    
    analyzer = RiskAnalyzer(llm_client=client)
    result = await analyzer.analyze_company(
        company_name="腾讯",
        company_info=mock_company_info,
        news_info=mock_news_info
    )
    
    print(f"✓ 分析完成!")
    print(f"   评分: {result.get('score')}")
    print(f"   风险等级: {result.get('risk_level')}")
    return True


async def main():
    print("\n" + "="*60)
    print("       EDR 模块功能测试")
    print("="*60)
    
    # 检查环境变量
    print("\n📋 环境变量检查:")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    print(f"   DEEPSEEK_API_KEY: {'✓ 已设置' if deepseek_key else '❌ 未设置'}")
    print(f"   TAVILY_API_KEY:   {'✓ 已设置' if tavily_key else '❌ 未设置'}")
    
    results = {}
    
    # 测试各组件
    if deepseek_key:
        results['DeepSeek'] = await test_deepseek_client()
    else:
        results['DeepSeek'] = False
        print("\n⚠️  跳过 DeepSeek 测试（未配置 API Key）")
    
    if tavily_key:
        results['Tavily'] = await test_tavily_client()
    else:
        results['Tavily'] = False
        print("\n⚠️  跳过 Tavily 测试（未配置 API Key）")
    
    # 如果两个 API 都配置了，测试完整流程
    if deepseek_key and tavily_key:
        print("\n是否进行完整分析测试？(需要30-60秒)")
        print("按 Enter 继续，或输入 'n' 跳过...")
        try:
            user_input = input().strip().lower()
            if user_input != 'n':
                results['完整分析'] = await test_full_analysis()
        except:
            pass
    else:
        # 使用模拟数据测试
        results['模拟分析'] = await test_mock_analysis()
    
    # 总结
    print_section("测试总结")
    for name, passed in results.items():
        status = "✓ 通过" if passed else "❌ 失败"
        print(f"   {name}: {status}")
    
    if not deepseek_key or not tavily_key:
        print("\n💡 提示：请配置 API 密钥以启用完整功能")
        print("   set DEEPSEEK_API_KEY=你的密钥")
        print("   set TAVILY_API_KEY=你的密钥")


if __name__ == "__main__":
    asyncio.run(main())

