import boto3
import json
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

def lambda_handler(event, context):
    #print("event: ", event)
    q = event.get('queryStringParameters', {}).get('q', '')
    if not q:
        #return {'statusCode': 200, 'body': json.dumps([])}
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                },
            'body': json.dumps([])
            }
    
    # Invoke Lex
    keywords = None
    try:
        keywords = extract_keywords_from_lex(q)
    except Exception as e:
        print(f"Lex error: {e}")
        return {'statusCode': 500, 'body': json.dumps({'error': 'Error processing request'})}
    print("keywords: ", keywords)
    if keywords:
        # Search OpenSearch
        try:
            results = search_photos(keywords)
            #return {'statusCode': 200, 'body': json.dumps(results)}
            return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                },
            'body': json.dumps(results)
            }
        except Exception as e:
            print(f"OpenSearch error: {e}")
            return {'statusCode': 500, 'body': json.dumps({'error': 'Error searching photos'})}
    else:
        # No keywords found
        #return {'statusCode': 200, 'body': json.dumps([])}
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                },
            'body': json.dumps([])
            }

def extract_keywords_from_lex(q):
    lex_client = boto3.client('lexv2-runtime')
    response = lex_client.recognize_text(
        botId='HSHM97HO7G',
        botAliasId='TSTALIASID',
        localeId='en_US',
        sessionId='testuser',
        text=q
    )
    return extract_keywords(response)

def extract_keywords(lex_response):
    interpretations = lex_response.get('interpretations', [])
    print("interpretations: ", interpretations)
    for interpretation in interpretations:
        intent = interpretation.get('intent', {})
        slots = intent.get('slots', {})
        keywords = []
        if slots:
            keyword_slot = slots.get('Keyword')
            keyword_2_slot = slots.get('Keyword_2')
            
            if keyword_slot and keyword_slot.get('value'):
                keywords.append(keyword_slot['value']['interpretedValue'])
            if keyword_2_slot and keyword_2_slot.get('value'):
                keywords.append(keyword_2_slot['value']['interpretedValue'])
        if keywords:
            return keywords
    return None

def get_opensearch_client():
    region = 'us-east-1'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)
    
    client = OpenSearch(
    hosts=[{'host': 'search-photos-m74gu5wpz62gg5csfse24gurki.us-east-1.es.amazonaws.com', 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    ssl_assert_hostname=False,
    ssl_show_warn=False,
    connection_class=RequestsHttpConnection
)
    return client

def search_photos(keywords):
    client = get_opensearch_client()
    index = 'photos'
    
    query = {
        'size': 25,
        'query': {
            'bool': {
                'should': [
                    {'match': {'labels': keyword}} for keyword in keywords
                ],
                'minimum_should_match': 1
            }
        }
    }
    
    response = client.search(body=query, index=index)
    results = [hit['_source'] for hit in response['hits']['hits']]
    return results
