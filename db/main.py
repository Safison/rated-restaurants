from fastapi import FastAPI,Response,status,HTTPException,Query 
from db.connection import connect_to_db, close_db_connection
from db.utils import format_restaurants
from pprint import pprint
from pydantic import BaseModel
from pg8000.exceptions import DatabaseError

app = FastAPI()

@app.exception_handler(DatabaseError)
def handle_db_errors(request, exc):
    print(exc)
    err_detail='Whoops! something went wrong on our end'
    raise HTTPException(status_code=500,detail=err_detail)



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
    website:str
    area_id : int
   

@app.patch('/api/restaurants/update/{restaurant_id}')
def update_restaurant(restaurant_id,update_restaurant:UpdateRestaurant,response:Response):
    conn = None
    try:
        conn = connect_to_db()
        query_string = """UPDATE restaurants SET area_id=:area_id, website=:website 
        where restaurant_id=:restaurant_id RETURNING *;"""
        update_dict = {}
        update_dict['restaurant_id'] = restaurant_id
        update_dict['area_id']=update_restaurant.area_id
        update_dict['website']=update_restaurant.website
            
        update_restaurant = conn.run(query_string, **update_dict)[0]
        restaurant_col = [col['name'] for col in conn.columns]
        formatted_restaurant = {
        restaurant_col[i]:update_restaurant[i]
        for i in range(len(restaurant_col))
        }
        return {'restaurant': formatted_restaurant}
    except IndexError:
        raise HTTPException(
        status_code = 404,
        detail = f'Restaurant with ID {restaurant_id} not found')
    finally:
        if conn:
            close_db_connection(conn)
    
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

@app.get("/api/getrestaurants/")
def search_restaurants(search: str):
    conn = connect_to_db()
    query_string = """SELECT * FROM restaurants WHERE lower(restaurant_name) LIKE lower(:search)"""
    search_str = f"%{search}%"
    filtered_rest = conn.run(query_string,search = search_str)
    rest_col = [col['name'] for col in conn.columns]
    formated_rest = dict(zip(rest_col,filtered_rest))
    return {'restaurants':formated_rest}

@app.get ('/api/sortrestaurants')
def sort(sort_by:str):
    conn = None
    try:
        conn = connect_to_db()
        query_string = """SELECT * FROM restaurants 
                        ORDER BY :sort_by DESC"""
        sort_str = f"{sort_by}"
        sorted_rest = conn.run(query_string,sort_by = sort_str)
        rest_col = [col['name'] for col in conn.columns]
        format_rest = dict(zip(rest_col, sorted_rest))
        return{'restaurants': format_rest}
    finally:
        if conn:
            close_db_connection(conn)
