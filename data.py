import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.font_manager as fm

plt.style.use('ggplot')
fp = fm.FontProperties(fname=r'c:\\windows\\fonts\\meiryo.ttc', size=16)

df_sample = pd.read_csv('restaurant.csv')
print(df_sample.mean(numeric_only=True))

# df_price = df_sample['予算']
# price_count = df_price.value_counts()
# price_count.plot.bar(alpha=0.8)
# plt.title('予算分布', FontProperties=fp)
# plt.savefig('price.png')
# plt.show()

# tables = df_sample['席数']
# plt.hist(tables, bins=10, alpha=0.6)
# plt.title('席数ヒストグラム', FontProperties=fp)
# plt.savefig('tables.png')
# plt.show()

# distance = df_sample['距離']
# plt.hist(distance, bins=10, alpha=0.6)
# plt.title('徒歩距離ヒストグラム', FontProperties=fp)
# plt.savefig('distance.png')
# plt.show()

# comments = df_sample['コメント数']
# comments_count = comments.value_counts()
# comments_count.plot.bar(alpha=0.8)
# plt.title('コメント数分布', FontProperties=fp)
# plt.savefig('comments.png')
# plt.show()

# df_sample.plot(kind='scatter', x='距離', y='予算')
# plt.title('徒歩距離と予算の相関', FontProperties=fp)
# plt.savefig('test.png')
# plt.show()

