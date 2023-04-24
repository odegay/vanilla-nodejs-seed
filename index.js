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
    const path = parsedUrl.pathname;
    const trimmedPath = path.replace(/^\/+|\/+$/g, '');
    const httpMethod = req.