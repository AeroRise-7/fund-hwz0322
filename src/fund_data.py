import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
from tqdm import tqdm
import datetime
from io import StringIO
import os
import json

# 定义缓存目录
# 使用绝对路径确保文件保存在根目录的data/fund_cache下
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/fund_cache")

def get_fund_info(fund_code):
    """获取基金基本信息，包括基金名称、公司、类型等"""
    try:
        # 初始化返回的字典
        fund_info = {
            'fund_name': '未获取到',
            'fund_company': '未获取到',
            'fund_type': '未获取到',
            'fund_code': fund_code,
            'is_money_fund': False,
            
            # 新增字段初始化
            'fund_manager': '未获取到',
            'fund_manager_id': '未获取到',
            'is_buy': False,
            'min_purchase': 0,
            'fund_short_name': '未获取到',
            'fund_company_id': '未获取到',
            'other_name': '',
            'update_date': '',
            'investment_themes': []
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # 首先尝试从基金详情页获取信息
        detail_url = f"http://fund.eastmoney.com/{fund_code}.html"
        response = requests.get(detail_url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 获取基金名称
        name_element = soup.find('div', class_='fundDetail-tit')
        if name_element:
            fund_info['fund_name'] = name_element.find('div').text.strip()
        
        # 查找基金信息表格
        info_table = soup.find('table', class_='info w790')
        if info_table:
            rows = info_table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                for i, cell in enumerate(cells):
                    text = cell.text.strip()
                    if '基金类型' in text and i + 1 < len(cells):
                        fund_type = cells[i + 1].text.strip()
                        fund_info['fund_type'] = fund_type
                        fund_info['is_money_fund'] = '货币型' in fund_type or '保本型' in fund_type
                    elif '基金管理人' in text and i + 1 < len(cells):
                        fund_info['fund_company'] = cells[i + 1].text.strip()
        
        # 如果从详情页获取不到完整信息，尝试使用搜索API
        if fund_info['fund_type'] == '未获取到' or fund_info['fund_company'] == '未获取到':
            search_url = f"http://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx?callback=&m=1&key={fund_code}"
            response = requests.get(search_url, headers=headers)
            
            try:
                data = response.json()
                if 'Datas' in data and len(data['Datas']) > 0:
                    for item in data['Datas']:
                        if item['CODE'] == fund_code:
                            if fund_info['fund_name'] == '未获取到':
                                fund_info['fund_name'] = item['NAME']
                            
                            # 添加新的字段
                            base_info = item.get('FundBaseInfo', {})
                            if base_info:
                                # 基金经理信息
                                fund_info['fund_manager'] = base_info.get('JJJL', '未获取到')
                                fund_info['fund_manager_id'] = base_info.get('JJJLID', '未获取到')
                                
                                # 申购相关信息
                                isbuy_value = base_info.get('ISBUY', '')
                                # 修正申购状态的判断逻辑：
                                # 1为可申购，2为暂停申购，空字符串或其他值为未知
                                if isbuy_value == '1':
                                    fund_info['is_buy'] = True
                                elif isbuy_value == '2' or isbuy_value == '0':
                                    fund_info['is_buy'] = False
                                else:
                                    fund_info['is_buy'] = None
                                
                                fund_info['min_purchase'] = base_info.get('MINSG', 0)
                                
                                # 其他基础信息
                                fund_info['fund_short_name'] = base_info.get('SHORTNAME', '未获取到')
                                fund_info['fund_company_id'] = base_info.get('JJGSID', '未获取到')
                                fund_info['other_name'] = base_info.get('OTHERNAME', '')
                                fund_info['update_date'] = base_info.get('FSRQ', '')
                                
                                # 直接使用FTYPE作为基金类型
                                if fund_info['fund_type'] == '未获取到':
                                    fund_type = base_info.get('FTYPE', '未知类型')
                                    fund_info['fund_type'] = fund_type
                                    # 更新is_money_fund标志，检查是否为货币型或保本型
                                    fund_info['is_money_fund'] = '货币型' in fund_type or '保本型' in fund_type
                                
                                if fund_info['fund_company'] == '未获取到':
                                    fund_info['fund_company'] = base_info.get('JJGS', '未获取到')
                            
                            # 添加主题投资信息
                            if 'ZTJJInfo' in item and item['ZTJJInfo']:
                                themes = []
                                for theme in item['ZTJJInfo']:
                                    themes.append({
                                        'type': theme.get('TTYPE', ''),
                                        'name': theme.get('TTYPENAME', '')
                                    })
                                fund_info['investment_themes'] = themes
                            
                            break
            except Exception as e:
                print(f"解析搜索API数据时发生错误: {str(e)}")
        
        return fund_info
        
    except Exception as e:
        print(f"获取基金信息时发生错误: {str(e)}")
        return {
            'fund_name': '未获取到',
            'fund_company': '未获取到',
            'fund_type': '未获取到',
            'fund_code': fund_code,
            'is_money_fund': False
        }

def map_fund_type_code(type_code):
    """将基金类型代码映射为可读的类型名称"""
    type_mapping = {
        '001': '股票型',
        '002': '混合型',
        '003': '债券型',
        '004': '指数型',
        '005': '保本型',
        '006': 'QDII',
        '007': 'LOF',
        '008': 'ETF',
        '009': '货币型',
    }
    
    # 处理组合类型代码（如"002,003"）
    if ',' in str(type_code):
        types = [type_mapping.get(t.strip(), '') for t in type_code.split(',')]
        return '/'.join(filter(None, types)) or '未知类型'
    
    return type_mapping.get(str(type_code), '未知类型')

def get_cached_fund_data(fund_code):
    """从本地缓存获取基金数据"""
    cache_file = os.path.join(CACHE_DIR, f"{fund_code}.csv")
    meta_file = os.path.join(CACHE_DIR, f"{fund_code}_meta.json")
    
    if os.path.exists(cache_file) and os.path.exists(meta_file):
        try:
            # 读取缓存数据
            df = pd.read_csv(cache_file)
            df['date'] = pd.to_datetime(df['date'])
            
            # 读取元数据
            with open(meta_file, 'r') as f:
                meta_data = json.load(f)
            
            # 检查最后更新时间
            last_update = pd.to_datetime(meta_data['last_update'])
            current_time = pd.to_datetime(datetime.datetime.now())
            
            # 如果今天已经更新过，直接返回缓存数据
            if last_update.date() == current_time.date():
                print(f"使用今日已更新的缓存数据（最后更新：{last_update.strftime('%Y-%m-%d %H:%M:%S')}）")
                return df, True  # 返回第二个参数表示是否是今日数据
            
            print(f"找到缓存数据（最后更新：{last_update.strftime('%Y-%m-%d %H:%M:%S')}），检查是否需要更新...")
            return df, False  # 返回第二个参数表示是否是今日数据
            
        except Exception as e:
            print(f"读取缓存数据时发生错误: {str(e)}")
            # 如果读取出错，删除可能损坏的缓存文件
            try:
                os.remove(cache_file)
                os.remove(meta_file)
            except:
                pass
    return None, False

def save_fund_data_to_cache(fund_code, df):
    """保存基金数据到本地缓存"""
    try:
        # 确保缓存目录存在
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        
        # 保存数据文件
        cache_file = os.path.join(CACHE_DIR, f"{fund_code}.csv")
        df.to_csv(cache_file, index=False)
        
        # 保存元数据
        meta_file = os.path.join(CACHE_DIR, f"{fund_code}_meta.json")
        meta_data = {
            'last_update': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'fund_code': fund_code,
            'data_count': len(df),
            'date_range': {
                'start': df['date'].min().strftime('%Y-%m-%d'),
                'end': df['date'].max().strftime('%Y-%m-%d')
            }
        }
        with open(meta_file, 'w') as f:
            json.dump(meta_data, f, indent=4)
        
        print(f"数据已缓存到: {cache_file}")
        
    except Exception as e:
        print(f"保存缓存数据时发生错误: {str(e)}")

def get_fund_data(fund_code, start_date=None, end_date=None, fill_missing=False):
    """获取基金历史净值数据，支持缓存和智能更新"""
    try:
        # 设置结束日期为当前日期
        if end_date is None:
            end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # 获取缓存数据
        cached_data, is_today = get_cached_fund_data(fund_code)
        
        if cached_data is not None:
            # 获取基金类型信息，判断是否为货币基金
            fund_info = get_fund_info(fund_code)
            is_money_fund = fund_info.get('is_money_fund', False)
            
            # 检查缓存数据是否包含累计净值（对于非货币基金）
            has_acc_nav = 'acc_nav' in cached_data.columns
            needs_acc_nav = not is_money_fund  # 非货币基金需要累计净值
            
            # 读取元数据信息
            meta_file = os.path.join(CACHE_DIR, f"{fund_code}_meta.json")
            with open(meta_file, 'r') as f:
                meta_data = json.load(f)
            
            if is_today and (has_acc_nav or not needs_acc_nav):
                # 如果是今天的数据且包含所需的累计净值数据(或者是货币基金不需要累计净值)，直接返回
                print(f"使用今日已更新的缓存数据（最后更新：{meta_data['last_update']}）")
                return cached_data
            elif is_today and needs_acc_nav and not has_acc_nav:
                # 如果是今天的数据但非货币基金缺少累计净值，需要重新获取
                print(f"缓存数据缺少累计净值，重新获取完整数据...")
                df = fetch_fund_data_from_api(fund_code, None, None)
                if not df.empty:
                    save_fund_data_to_cache(fund_code, df)
                return df
            
            # 获取缓存的最后一个日期
            last_cache_date = cached_data['date'].max()
            current_date = pd.to_datetime(end_date)
            
            # 如果缓存数据不是最新的，获取增量更新
            if current_date.date() > last_cache_date.date():
                # 获取元数据里的最后更新时间
                last_update = pd.to_datetime(meta_data['last_update'])
                current_time = pd.to_datetime(datetime.datetime.now())
                
                # 计算最后更新时间与当前时间的时间差（小时）
                hours_diff = (current_time - last_update).total_seconds() / 3600
                
                # 如果最后更新时间在24小时内，且今天不是交易日或者最后一个交易日就是缓存数据的最后日期，则不更新
                today = datetime.datetime.now().date()
                is_weekend = today.weekday() >= 5  # 周六和周日
                
                # 判断是否需要更新
                if hours_diff < 24 and (is_weekend or last_cache_date.date() == pd.to_datetime(end_date).date()) and (has_acc_nav or not needs_acc_nav):
                    print(f"缓存数据已在24小时内更新过（{last_update.strftime('%Y-%m-%d %H:%M:%S')}），无需频繁更新")
                    df = cached_data
                    return df
                
                print(f"缓存数据需要更新，获取 {last_cache_date.strftime('%Y-%m-%d')} 之后的数据...")
                # 获取增量数据
                increment_start = (last_cache_date + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                new_data = fetch_fund_data_from_api(fund_code, increment_start, end_date)
                
                if not new_data.empty:
                    # 判断新数据中是否包含累计净值
                    includes_acc_nav = 'acc_nav' in new_data.columns
                    
                    # 判断缓存数据是否包含累计净值，如果不包含但新数据中有，则需要重新获取完整数据
                    if includes_acc_nav and not has_acc_nav and needs_acc_nav:
                        print("检测到新数据包含累计净值而缓存数据不包含，重新获取完整数据...")
                        df = fetch_fund_data_from_api(fund_code, None, None)
                        if not df.empty:
                            save_fund_data_to_cache(fund_code, df)
                        return df
                    
                    # 合并新旧数据
                    df = pd.concat([cached_data, new_data], ignore_index=True)
                    df = df.drop_duplicates(subset=['date']).sort_values('date')
                    # 更新缓存
                    save_fund_data_to_cache(fund_code, df)
                    print("缓存数据已更新")
                else:
                    print("没有新数据需要更新")
                    df = cached_data
            else:
                # 即使缓存数据是最新的，如果是非货币基金但缺少累计净值，也需要重新获取
                if needs_acc_nav and not has_acc_nav:
                    print("缓存数据缺少累计净值，重新获取完整数据...")
                    df = fetch_fund_data_from_api(fund_code, None, None)
                    if not df.empty:
                        save_fund_data_to_cache(fund_code, df)
                    return df
                
                print("缓存数据已是最新，无需更新")
                df = cached_data
        else:
            # 获取完整历史数据
            print(f"未找到缓存数据，开始获取基金{fund_code}的完整历史数据...")
            df = fetch_fund_data_from_api(fund_code, None, None)  # 不需要传入日期参数
            if not df.empty:
                save_fund_data_to_cache(fund_code, df)
        
        # 填充非交易日数据
        if fill_missing and not df.empty:
            # 检查是否存在acc_nav列
            has_acc_nav = 'acc_nav' in df.columns
            
            date_range = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='D')
            df = df.set_index('date').reindex(date_range)
            df = df.ffill()  # 使用ffill()替代fillna(method='ffill')
            df = df.reset_index().rename(columns={'index': 'date'})
        
        return df
    
    except Exception as e:
        print(f"获取基金数据时发生错误: {str(e)}")
        return pd.DataFrame()

def fetch_fund_data_from_api(fund_code, start_date, end_date):
    """从API获取基金数据，使用分页方式从最新日期往前滚动获取"""
    all_data = pd.DataFrame()
    page = 1
    per_page = 20  # 每页数据量，东方财富默认20条
    
    print(f"开始获取基金{fund_code}的历史数据...")
    if start_date:
        print(f"获取日期范围: {start_date} 至 {end_date}")
    
    # 首先获取基金类型
    try:
        fund_info = get_fund_info(fund_code)
        is_money_fund = fund_info.get('is_money_fund', False)
    except Exception as e:
        print(f"获取基金类型时发生错误: {str(e)}")
        is_money_fund = False
    
    while True:
        try:
            # 构建API URL，添加分页参数和日期参数
            url = f"http://fund.eastmoney.com/f10/F10DataApi.aspx?type=lsjz&code={fund_code}&per={per_page}&page={page}"
            
            # 添加日期参数
            if start_date:
                url += f"&sdate={start_date}&edate={end_date}"
            
            # 发送请求获取数据
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            
            # 检查是否有"暂无数据"
            if "暂无数据" in response.text:
                print(f"已获取所有数据")
                break
            
            # 使用StringIO包装HTML内容
            try:
                df = pd.read_html(StringIO(response.text))[0]
            except Exception as e:
                print(f"解析HTML表格时发生错误: {str(e)}")
                if page == 1:
                    return pd.DataFrame()
                break
            
            # 如果没有数据了，退出循环
            if df.empty:
                break
            
            # 根据基金类型处理不同的列名
            if is_money_fund:
                # 货币基金的列名通常是：净值日期、每万份收益、7日年化收益率(%)等
                df.columns = ['date', 'nav', 'annual_return', 'subscription_status', 'redemption_status', 'dividend'] \
                    if len(df.columns) == 6 else ['date', 'nav', 'annual_return', 'subscription_status', 'redemption_status']
            else:
                # 其他基金的列名通常是：净值日期、单位净值、累计净值、日增长率等
                df.columns = ['date', 'nav', 'acc_nav', 'daily_return', 'subscription_status', 'redemption_status', 'dividend'] \
                    if len(df.columns) == 7 else ['date', 'nav', 'acc_nav', 'daily_return', 'subscription_status', 'redemption_status']
            
            # 转换日期列
            df['date'] = df['date'].replace({'\\*': ''}, regex=True)  # 移除星号
            df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
            
            # 转换净值列为数值类型
            df['nav'] = df['nav'].replace({'\\*': '', ',': ''}, regex=True)  # 移除星号和逗号
            df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
            
            # 转换累计净值列为数值类型（对于非货币基金）
            if not is_money_fund and 'acc_nav' in df.columns:
                df['acc_nav'] = df['acc_nav'].replace({'\\*': '', ',': ''}, regex=True)
                df['acc_nav'] = pd.to_numeric(df['acc_nav'], errors='coerce')
            
            # 合并数据
            if is_money_fund:
                all_data = pd.concat([all_data, df[['date', 'nav']]], ignore_index=True)
            else:
                # 对于非货币基金，保存单位净值和累计净值
                all_data = pd.concat([all_data, df[['date', 'nav', 'acc_nav']]], ignore_index=True)
            
            print(f"第{page}页: 获取到{len(df)}条数据，最早日期: {df['date'].min().strftime('%Y-%m-%d')}")
            
            # 检查是否还有下一页（通过数据量判断）
            if len(df) < per_page:
                print("已到达最后一页")
                break
            
            # 下一页
            page += 1
            
            # 添加延迟，避免请求过于频繁
            time.sleep(0.5)
            
        except Exception as e:
            print(f"获取第 {page} 页数据时发生错误: {str(e)}")
            if page == 1:
                return pd.DataFrame()
            break
    
    if not all_data.empty:
        # 删除无效数据并排序
        all_data = all_data.dropna(subset=['date', 'nav'])
        all_data = all_data.sort_values('date')
        all_data = all_data.drop_duplicates(subset=['date'])
        print(f"共获取到 {len(all_data)} 条数据记录，日期范围：{all_data['date'].min().strftime('%Y-%m-%d')} 至 {all_data['date'].max().strftime('%Y-%m-%d')}")
    
    return all_data