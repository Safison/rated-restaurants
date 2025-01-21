from fastapi import FastAPI,Response,status
from db.connection import connect_to_db, close_db_connection
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
    raw_restaurants = conn.run("""select restaurants.restaurant_id, restaurant_name, area_id,cuisine, 
                               website,avg(rating) AS average_rating 
                               from restaurants 
                               join ratings 
                               on restaurants.restaurant_id = ratings.restaurant_id
                               GROUP BY restaurants.restaurant_id;
                               ;""")
   

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
    inserted_restaurant = conn.run(query_string,**new_restaurant.model_dump())[0]
    restaurant_coulmns= [col['name'] for col in conn.columns]
    close_db_connection(conn)
    formatted_restaurant = dict(zip(restaurant_coulmns, inserted_restaurant))
    return {'restaurant':formatted_restaurant}

@app.delete('/api/restaurant/{restaurant_id}',status_code=204)
def delete_restaurant(restaurant_id):
    conn = connect_to_db()
    query_string = """DELETE FROM restaurants 
    where restaurant_id=:restaurant_id;"""
    deleted_restaurant = conn.run(query_string, restaurant_id=restaurant_id)
    close_db_connection(conn)
    
class UpdateRestaurant(BaseModel):
    area_id : int
   

@app.patch('/api/restaurants/update/{restaurant_id}')
def update_restaurant(restaurant_id,update_restaurant:UpdateRestaurant,response:Response):
    conn = connect_to_db()
    restaurants_ids = conn.run("SELECT restaurant_id FROM restaurants;")
    print(restaurants_ids)
    id_check_result = any(restaurant_id in sublist for sublist in restaurant_id)
    print(id_check_result)
    print(restaurant_id)
    if not id_check_result:
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        query_string = """UPDATE restaurants SET area_id=:area_id 
        where restaurant_id=:restaurant_id RETURNING *;"""
        update_dict = {}
        update_dict['restaurant_id'] = restaurant_id
        update_dict['area_id']=update_restaurant.area_id
        
        update_restaurant = conn.run(query_string, **update_dict)[0]
        restaurant_col = [col['name'] for col in conn.columns]
        formatted_restaurant = {
            restaurant_col[i]:update_restaurant[i]
            for i in range(len(restaurant_col))
        }
        return {'restaurant': formatted_restaurant}
    
@app.get('/api/areas/{area_id}/restaurants')
def get_area_with_restaurants(area_id):
    conn = connect_to_db()
    restaurants_query_string = """SELECT * FROM restaurants WHERE area_id=:area_id"""
    area_restaurants = conn.run(restaurants_query_string, area_id=area_id)
    restaurant_col = [col['name'] for col in conn.columns]
    formatted_restaurant = format_restaurants(area_restaurants, restaurant_col)
    
    area_query_string = """SELECT * FROM areas WHERE area_id=:area_id"""
    area_list = conn.run(area_query_string, area_id=area_id)
    area_col = [col['name'] for col in conn.columns]
    close_db_connection(conn)
    formatted_area = dict(zip(area_col, area_list))
    formatted_area['total_restaurants'] = len(area_restaurants)
    formatted_area['restaurants'] = formatted_restaurant
    return formatted_area

