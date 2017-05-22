var React = require('react');
var _ = require('lodash');
var api = require('utils/api');
var cache = require('utils/cache');
var Loading = require('components/Loading');
var Alert = require('components/Alert');
var Card = require('components/manga/Card');

var CardList = React.createClass({
    renderCard: function (card, index){
        return(
            <Card manga={card}/>
        );
    },

    render: function() {
        return(
            <div className="latest-list">
                <div className="title-green">Search Result Manga</div>
                <Loading loading={this.props.fetching} />
            {this.props.manga.map(this.renderCard)}
            </div>
        );
    }
});

var search = React.createClass({
    statics: {
        fetchData: function(token, params, query) {
            var url = '/search?q=' + params.q;
            return api.get(url, token).then((data)=> {
                // cache.expire(token, url);
                return data;
            }).then(null ,
                function(){
                    return {error: true};
                });
        }
    },

    componentWillReceiveProps: function(nextProps){
        var data = nextProps.data.search;
        data.error ? this.setState({fetching: false}): this.fetchCards(data);
    },

    componentDidMount: function (){
        var data = this.props.data.search;
        data.error ? this.setState({fetching: false}): this.fetchCards(data);
    },

    getInitialState: function () {
        return {
            cards : [],
            fetching: false
        }
    },

    fetchCards: function (data) {
        var newState = this.state;
        newState.cards = [];
        newState.fetching = true;
        this.setState(newState);
        this.updateCardsData(data);
    },

    updateCardsData: function (data) {
        this.setState({
            cards: data,
            fetching: false
        });
    },

    render: function() {
        var data =  this.props.data.search;
        return (
            <div>
                <div className="container">
                    <div className="row">
                    { data.error ? <Alert msg={'There some image cannot be loaded for this chapter'} />: 
                        <CardList manga={this.state.cards} fetching={this.state.fetching} />
                    }
                    </div>
                </div>
            </div>
        );
    }
});

module.exports = search;