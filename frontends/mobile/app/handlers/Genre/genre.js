/** @flow */

import React, { Component, PropTypes, findDOMNode} from'react';
import { Link } from 'react-router';
import router from 'utils/router';

import _ from 'lodash';
import api from 'utils/api';
import cache from 'utils/cache';
import LoadingUI from 'components/LoadingUI';

import Card from 'components/manga/Card';

class CardList extends Component {
    renderCard(card, index){
        return(
            <Card manga={card}/>
            );
    }

    render() {
        return(
            <div className="latest-list">
                <div className="title-green">Genre Manga</div>
                <LoadingUI loading={this.props.fetching} />
                {this.props.manga.map(this.renderCard.bind(this))}
            </div>
            );
    }
}

CardList.propsTypes = {
    manga: PropTypes.array,
    fetching: PropTypes.bool
}

class Genre extends Component {
    constructor() {
        super();
        this.state = {
            cards : [],
            fetching: true
        }

        this.fetchCards = this.fetchCards.bind(this);
        this.updateCardsData = this.updateCardsData.bind(this);
    }

    componentWillReceiveProps(nextProps){
        let data = nextProps.data.genre;
        data.error ? this.setState({fetching: false}): this.fetchCards(data);
    }

    componentDidMount(){
        let data = this.props.data.genre;
        data.error ? this.setState({fetching: false}): this.fetchCards(data);
    }

    fetchCards(data) {
       let newState = this.state;
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
        let data =  this.props.data.genre;
        return (
            <div>
                <div className="container">
                    <div className="row">
                    { data.error ? <AlertUI msg={'Ooopss! there is no manga series'} />:
                        <CardList manga={this.state.cards} fetching={this.state.fetching} />
                    }
                    </div>
                </div>
            </div>
        );
    }
}

Genre.fetchData = (token, params, query) => {
    let url = '/genre?q=' + params.q;
    return api.get(url, token).then((data) => {
        return data;
    }).then(null ,
    function(){
        return {error: true};
    });
}

export default Genre;