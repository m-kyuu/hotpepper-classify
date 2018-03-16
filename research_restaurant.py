import logging
from bs4 import BeautifulSoup
import requests
import time
import re
import os
from pandas import Series, DataFrame
from tqdm import tqdm

_URL = 'https://www.hotpepper.jp/SA11/fwt%E6%B1%A0%E8%A2%8B/'
_DOMAIN = 'https://www.hotpepper.jp'
_FILE_NAME = 'restaurant.csv'

# ログファイル
logger_fh = logging.getLogger('Log')
logger_fh.setLevel(20)
fh = logging.FileHandler('log.log')
logger_fh.addHandler(fh)
# 標準出力
logger_sh = logging.getLogger('Standard out')
logger_sh.setLevel(20)
sh = logging.StreamHandler()
logger_sh.addHandler(sh)
# format
formatter = logging.Formatter('%(asctime)s:%(lineno)d:%(levelname)s:%(message)s')
fh.setFormatter(formatter)
sh.setFormatter(formatter)


def _get_url():
    logger_fh.log(20, 'Start searching')

    result = requests.get(_URL)
    soup = BeautifulSoup(result.text, 'html.parser')

    # ページ数を取得
    body = soup.find('body')
    pages = body.find_all('div', {'class': 'pageLinkWrapBasic'})
    pages_text = str(pages)
    pages_split = pages_text.split('</li>\n<li>\n')
    page_split = pages_split[-2]
    m = re.search('(?<=\n\t)\d+', page_split)
    page = int(m.group(0))

    logger_fh.log(20, 'Find ' + str(page) + ' pages')
    logger_sh.log(20, 'Find ' + str(page) + ' pages')

    # ページのリストを生成
    pages_url = [_URL]
    for i in range(2, page + 1):
        pages_url.append('{url}bgn{page}/'.format(url=_URL, page=str(i)))

    return pages_url


# お店情報を取得
def _get_info(url, area):
    name = []
    link = []
    access = []
    distance = []
    price = []
    tables = []
    room = []
    keywords = []
    comment_num = []
    comment = []

    result = requests.get(url)
    soup = BeautifulSoup(result.text, 'html.parser')
    detail_list = soup.find_all('div', {'class': 'shopDetailText'})

    for detail in tqdm(detail_list):
        # 店舗名
        title = detail.find('h3', {'class': 'shopDetailStoreName'})
        title_text = title.a.string.replace('\u3000', ' ')
        name.append(title_text)

        # リンク
        title_link = title.a.get('href')
        link.append(_DOMAIN + title_link)

        # キーワード
        keyword = detail.find('p', {'class': 'shopDetailGenreCatch'}).string
        keyword = keyword.strip()
        keyword = keyword.replace('\u3000', ' ')
        keywords.append(keyword)

        # 駅
        station_text = detail.find('li', {'class': 'shopDetailInfoAccess'}).string.strip()
        m = re.search('.*?(?=駅)', station_text)
        if m:
            station = m.group(0).replace('\u3000', '') + '駅'
        else:
            station = ''
        access.append(station)

        # 距離
        m_dis = re.search('\d+(?=分)', station_text)
        if m_dis:
            dis = m_dis.group(0)
        else:
            dis = '-1'
        distance.append(int(dis))

        # 値段（複数ある場合は最大値を採用）
        price_text = detail.find('li', {'class': 'shopDetailInfoBudget'}).string.strip()
        pattern = re.compile('\d+,?\d+(?=円)')
        price_str = [item.replace(',', '') for item in pattern.findall(price_text)]
        price_list = [int(i) for i in price_str]
        if len(price_list) == 1:
            price_max = price_list[0]
        elif len(price_list) > 1:
            price_max = max(price_list)
        else:
            price_max = 0
        price.append(price_max)

        # 席数
        table_text = detail.find('li', {'class': 'shopDetailInfoCapacity'}).string.strip()
        m_table = re.search('\d+(?=席)', table_text)
        if m_table:
            table = m_table.group(0)
        else:
            table = '0'
        tables.append(int(table))

        room_page, comment_num_page, comment_page = _get_comment(_DOMAIN + title_link)
        room.append(room_page)
        comment_num.append(comment_num_page)
        comment.append(comment_page)

        time.sleep(3)

    # シリーズ化
    name = Series(name)
    link = Series(link)
    access = Series(access)
    distance = Series(distance)
    price = Series(price)
    tables = Series(tables)
    keywords = Series(keywords)
    comment_num = Series(comment_num)
    comment = Series(comment)

    # データフレームを作成
    restaurant_df = DataFrame({'地区': area,
                               '店舗名': name,
                               'リンク': link,
                               '最寄り駅': access,
                               '距離': distance,
                               '予算': price,
                               '席数': tables,
                               '個室': room,
                               'キーワード': keywords,
                               'コメント数': comment_num,
                               'コメント': comment},
    columns=['地区', '店舗名', 'リンク', '最寄り駅', '距離', '予算', '席数', '個室', 'キーワード', 'コメント数', 'コメント'])

    logger_sh.log(20, 'outputting...')

    if not os.path.exists(_FILE_NAME):
        restaurant_df.to_csv(_FILE_NAME, index=False, encoding='utf-8')
    else:
        restaurant_df.to_csv(_FILE_NAME, index=False, encoding='utf-8', mode='a', header=False)


# 店舗ページで情報取得
def _get_comment(url):
    result = requests.get(url)
    soup = BeautifulSoup(result.text, 'html.parser')

    # 個室
    room_table = soup.find_all('div', {'class': 'shopInfoDetail'})[1]
    room_tr = room_table.find_all('tr')[2]
    room_text = room_tr.find('td').string.strip()
    pattern_room = re.compile('^(あり|なし)(?=.*)')
    room = pattern_room.match(room_text).group(0)

    # コメント数とコメント内容
    # コメント数が表示されていない場合はスキップ
    comment_text = soup.find('p', {'class': 'recommendReportNum'})
    comment = ''
    comment_num = 0
    if comment_text is not None:
        detail_url = url + 'report/'
        result_detail = requests.get(detail_url)
        comment_html = BeautifulSoup(result_detail.text, 'html.parser')
        page_text = comment_html.find('ul', {'class': 'pageLinkLinear cf'})
        # コメント数はあるが、全部メニューレポートの場合もスキップ
        if page_text is None:
            return (room, comment_num, comment)
        page_li = page_text.find_all('li')
        page_num_text = page_li[-1]
        if page_num_text.a is None:
            page_num = 1
        elif page_num_text.a.string == '...':
            page_num = int(page_li[-2].a.string) + 1
        else:
            page_num = int(page_num_text.a.string)
        comment_list = []
        for index in range(1, page_num + 1):
            if index == 1:
                comment_list.extend(_get_comment_detail(comment_html))
                time.sleep(3)
            else:
                page = 'list_' + str(((index - 1) * 5) + 1)
                page_url = detail_url + page
                result_page = requests.get(page_url)
                page_html = BeautifulSoup(result_page.text, 'html.parser')
                comment_list.extend(_get_comment_detail(page_html))
                time.sleep(3)
        comment_num = len(comment_list)
        comment = ' '.join(comment_list)

    return (room, comment_num, comment)


# 各ページのコメントを抽出
def _get_comment_detail(page_html):
    # コメントタイトル抽出
    comment = []
    title_html = page_html.find_all('h2', {'class': 'recommendReportTitle'})
    for title in title_html:
        comment.append(title.a.string)

    # コメント抽出
    comment_text = page_html.find_all('p', {'class': 'recommendReportText'})
    for i, item in enumerate(comment_text, 0):
        comment_detail = ''
        for string in item.strings:
            comment_detail += string.strip()
        comment[i] += ' ' + comment_detail
    return comment


if __name__ == '__main__':
    urls = _get_url()
    for index, url in enumerate(urls):
        if index == 10:
            break
        logger_sh.log(20, str(index+1) + ' page now ' + url)
        _get_info(url, '池袋')
    logger_fh.log(20, 'End')

