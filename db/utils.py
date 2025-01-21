
def format_restaurants(data, columns_headings):
    formatted_restaurants = []
    for row in data:
        formatted_row = {}
        for i in range(len(columns_headings)):
            formatted_row[columns_headings[i]] = row[i]
        formatted_restaurants.append(formatted_row)
    return formatted_restaurants
