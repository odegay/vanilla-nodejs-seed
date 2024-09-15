import * as http from 'http';
import * as url from 'url';
import * as string_decoder from 'string_decoder';
import { handlers } from './lib/handlers';
import { helpers } from './lib/helpers';
import { env } from './ecosystem.config';

function test2 (asdasd: string, sdsds: string) {
    return asdasd + sdsds;
}

const server = http.createServer((req, res) => {

    const parsedUrl = url.parse(req.url, true);    
    const trimmedPath = 'test';
    const httpMethod = req.method;
    const queryStringParamsObject = parsedUrl.query;
    const headers = req.headers;
    const decoder = new string_decoder.StringDecoder('utf-8');
    let buffer = '';

    req.on('data', (data: any) => {