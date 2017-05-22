/** @flow */

import React, { Component, PropTypes, findDOMNode} from'react';

import _ from 'lodash';
import api from 'utils/api';
import cache from 'utils/cache';

import AlertUI from 'components/AlertUI';
import LoadingUI from 'components/LoadingUI';
import Card from 'components/manga/Card';


class CardList extends Component {
    renderCard(card, index){
        return(
            <Card manga={card}/>
        );
    }

    render(): any {
        return(
            <div className="latest-list">
                <div className="title-green">Search Result Manga</div>
                <LoadingUI loading={this.props.fetching} />
            {this.props.manga.map(this.renderCard)}
            </div>
        );
    }
}

CardList.propTypes = {
    fetching: PropTypes.bool,
    manga: PropTypes.array
}

class Search extends Component {
    constructor(props) {
        super(props);
        this.state = {
            cards : [],
            fetching: false
        }
    }

    componentWillReceiveProps(nextProps){
        var data = nextProps.data.search;
        data.error ? this.setState({fetching: false}): this.fetchCards(data);
    }

    componentDidMount(){
        var data = this.props.data.search;
        data.error ? this.setState({fetching: false}): this.fetchCards(data);
    }

    fetchCards(data) {
        var newState = this.state;
        newState.cards = [];
        newState.fetching = true;
        this.setState(newState);
        this.updateCardsData(data);
    }

    updateCardsData(data) {
        this.setState({
            cards: data,
            fetching: false
        });
    }

    render(): any {
        var data =  this.props.data.search;
        return (
            <div className="container">
                <div className="row">
                { data.error ? <AlertUI msg={'There some image cannot be loaded for this chapter'} />: 
                    <CardList manga={this.state.cards} fetching={this.state.fetching} />
                }
                </div>
            </div>
        );
    }
}

Search.fetchData = (token, params, query) => {
    var url = '/search?q=' + params.q;
    return api.get(url, token).then((data)=> {
        // cache.expire(token, url);
        return data;
    }).then(null ,
    function(){
        return {error: true};
    });
}

export default Search;