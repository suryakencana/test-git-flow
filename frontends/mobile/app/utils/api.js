import { Promise } from 'when';
import axios from 'axios';
import cache from './cache';

// var HOST = 'http://addressbook-api.herokuapp.com';
// var HOST = 'http://localhost:5000';
var HOST = '/api/1.0';

exports.get = (url, token) => {
  var cached = cache.get(token, url);
  return (cached) ?
    Promise.resolve(cached) :
    axios({
      url: HOST+url,
      headers: { 'Authorization': token }
    }).then(function(res) {
      cache.set(token, url, res.data);
      return res.data;
    });
};

exports.post = (url, data, token) => {
  return axios({
    method: 'post',
    data: data,
    url: HOST+url,
    headers: { 'Authorization': token }
  }).then(function(res) {
    return res.data;
  });
};
