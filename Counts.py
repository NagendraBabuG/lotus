import pandas as pd


df = pd.read_csv('your_file.csv')


column_3_counts = df.iloc[:, 2].value_counts()


count_1 = column_3_counts.get(1, 0)
count_0 = column_3_counts.get(0, 0)


print(f"Rows with 1 : {count_1}")
print(f"Rows with 0 : {count_0}")
