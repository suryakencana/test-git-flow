/** @flow */

import React, { Component, PropTypes, findDOMNode} from'react';

import _ from 'lodash';
import api from 'utils/api';
import cache from 'utils/cache';

import MsgBox from 'components/MsgBox';
import LoadingUI from 'components/LoadingUI';
import InfiniteScroll from 'components/scroller/InfiniteScroll';
import Card from 'components/manga/Card';

import { connect } from 'react-redux';
import { resetErrorMessage, MessageBox } from 'actions';


class Latest extends Component {
    constructor(props) {
        super(props);
        this.state = {
            limit: 10,
            offset: 0,
            cards : [],
            fetching: false,
            error: false
        };

        this.fetchCards = this.fetchCards.bind(this);
        this.updateCardsData = this.updateCardsData.bind(this);
        this._onRequestMoreItems = this._onRequestMoreItems.bind(this);
        this._onScroll = this._onScroll.bind(this);
    }

    fetchCards() {
        let newState = this.state;
        newState.fetching = true;

        this.setState(newState);

        let self = this;
        let url = '/latest?page=' + newState.offset + '&cards=' + newState.limit;
        let result = api.post(url, this.props.token).then((data) => {
            cache.expire(this.props.token, url);
            self.updateCardsData(data);
            self.setState({fetching: false});
        }).then(null, function(){
            self.setState({
                fetching: false,
                error: true
            });
        });
    }

    updateCardsData(data) {
        this.setState({
            cards: this.state.cards.concat(data),
            offset: this.state.offset + 1
        });
    }

    _onRequestMoreItems(){
        this.fetchCards();
    }

    _onScroll(e) {

    }
    
    renderCard(card, index){
        return <Card manga={card} key={index}/>;
    }

    render(): any {
        return(       
            <div className="row">
                <div className="latest-list">
                <div className="title-green">Latest Manga</div>
                { this.state.error ? <MsgBox log='alert' messageText='There some request on server cannot be loaded for this pages'/> :
                <InfiniteScroll
                onScroll={this._onScroll}
                hasMore={true}
                onRequestMoreItems={this._onRequestMoreItems}
                threshold={250}
                style={styles.messagesList}>
                <center>
                {this.state.cards.map(this.renderCard)}
                </center>
                </InfiniteScroll>
                }
                </div>
                <LoadingUI loading={this.state.fetching} />
            </div>
            );
    }
}

let styles = {
    wrapperList: {
        height: '250px',
        overflow: 'hidden'
    },
    messagesList: {
        height: '100%'
    },
}

function mapStateToProps(state) {
  return {
    errorMessage: state.errorMessage
  }
}

export default connect(
  mapStateToProps,
  { MessageBox }
  )(Latest);