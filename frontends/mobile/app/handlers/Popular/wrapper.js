/** @flow */

import React, {Component, PropTypes, findDOMNode } from 'react';

import Popular from './index';

export default class Wrapper extends Component {
  render(): any {
    return (
      <div className="container">
        <Popular />
      </div>
      );
  }
}