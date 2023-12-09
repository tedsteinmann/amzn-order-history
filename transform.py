import pandas as pd

accountName='personal'


# Load the CSV files
items = pd.read_csv(f'{accountName}/items.csv')
orders = pd.read_csv(f'{accountName}/orders.csv')

# Merge the files on 'orderNumber'
merged_csv = pd.merge(items, orders, on='orderNumber')

# Convert 'date_column' to datetime format (if it's not already)
merged_csv['orderPlacedDate'] = pd.to_datetime(merged_csv['orderPlacedDate'])

# Example: Update the datetime to a different format, e.g., ISO format
merged_csv['orderPlacedDate'] = merged_csv['orderPlacedDate'].dt.strftime('%Y-%m-%d')

order_items = merged_csv[['orderNumber','itemQuantity','itemDescription','itemSeller','itemCondition','itemPrice','orderPlacedDate']]

order_items.to_csv(f'{accountName}/order_items.csv', index=False)

