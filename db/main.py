from fastapi import FastAPI
from db.connection import connect_to_db, close_db_connection
import json
from db.utils import format_restaurants
app = FastAPI()
from pprint import pprint
from pydantic import BaseModel

@app.get('/healthcheck')
def get_healthcheck():
    
    return {"message": "all ok"}

@app.get('/api/restaurants')
def get_restaurants():
    conn = connect_to_db()
    raw_restaurants = conn.run('SELECT * FROM restaurants;')
    pprint(raw_restaurants)
    columns = [col['name'] for col in conn.columns]
    formated_restaurants = format_restaurants(raw_restaurants, columns)
    close_db_connection(conn)
    return {'restaurants':formated_restaurants}

class NewRestaurants(BaseModel):
    restaurant_name: str
    area_id: int
    cuisine: str
    website: str

@app.post('/api/restaurants')
def add_restaurant(new_restaurant:NewRestaurants):
    restaurant_dict = {}
    conn = connect_to_db()
    query_string = ("""INSERT INTO restaurants (restaurant_name, area_id,cuisine,website) 
             VALUES (:restaurant_name, :area_id,:cuisine,:website) 
             RETURNING *;""")
    restaurant_dict['restaurant_name'] = new_restaurant.restaurant_name
    restaurant_dict['area_id'] = new_restaurant.area_id
    restaurant_dict['cuisine'] = new_restaurant.cuisine
    restaurant_dict['website'] = new_restaurant.website
    inserted_restaurant = conn.run(query_string,**restaurant_dict)[0]
    restaurant_coulmns= [col['name'] for col in conn.columns]
    formatted_restaurant = {
        restaurant_coulmns[i]: inserted_restaurant[i]
        for i in range(len(restaurant_coulmns)) 
    }
    return {'restaurant':formatted_restaurant}



    pass
