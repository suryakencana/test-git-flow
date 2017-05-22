/** @flow */

import React, { Component, PropTypes} from'react';
import { Route, DefaultRoute, RouteHandler, Link } from 'react-router';
import router from 'utils/router';
import SearchBox from 'components/SearchBox';


class Navbar extends Component {

    constructor(){
        super();
        this.state = { query: ''};
        this._handleSearch = this._handleSearch.bind(this);
        this._handleChange = this._handleChange.bind(this);
    }

    _handleSearch(query){
        if (!query || query.trim().length < 2) {
            return;
        }
        router.transitionTo('search', {q: query});
        this.setState({query: ''});
    }

    _handleChange(query){
        this.setState({query: query});
    }

    render(): any {
        return (
            <div className="navbar navbar-fixed-top">
                <div className="navbar-inner">
                    <div className="container">
                    {this.props.menuBar}
                         <SearchBox
                        onQueryChange={this._handleChange}
                        onQuerySubmit={this._handleSearch}
                        query={this.state.query}
                        placeholder="Searching series name..."
                        />
                    </div>
                </div>
            </div>
        );
    }
}

Navbar.propTypes = {
    genres: PropTypes.array,
    menuBar: PropTypes.element
};

export default Navbar;