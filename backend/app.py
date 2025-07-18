from flask import Flask
from flask_openapi3 import OpenAPI, Info, Tag

info = Info(title='DungeonEconomist API', version='1.0.0')
app = OpenAPI(__name__, info=info)

health_tag = Tag(name='Health', description='Health check endpoint')

@app.get('/health', tags=[health_tag])
def health_check():
    return {'status': 'ok'}

if __name__ == '__main__':
    app.run(debug=True)