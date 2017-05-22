/** @flow */

import React, { Component, PropTypes, findDOMNode} from'react';
import { Link } from 'react-router';

import _ from 'lodash';
import api from 'utils/api';
import cache from 'utils/cache';
import LoadingUI from 'components/LoadingUI';


class ChapterList extends Component {
    constructor(props) {
        super(props);
        this._renderItem = this._renderItem.bind(this);
    }

    _renderItem() {
       let results =  _.map(this.props.chapters, function(chapter){
            let href = chapter.url.split('/');
            return (
                <Link to="chapter" params={{seriesSlug: href[0], chapterSlug: href[1]}} className="list-group-item">
                <span>{chapter.name}</span><span className="pull-right">{chapter.time}</span>
                </Link>
            );
        });
       return results;
    }

    render() {
        return (
            <div className="col-xs-12 list-group">
             {this._renderItem()}
            </div>
        );
    }
}

ChapterList.propTypes = {
    chapters: PropTypes.array
}

class Pages extends Component {
    constructor(props) {
        super(props);
        this._renderTags = this._renderTags.bind();
    }

    _renderTags(tags){
       return tags.map(function(item){
           return (<div className="ticket"><Link to="genre" params={{q: item.value}}><i className="fa fa-tag fa-lg fa-fw"></i>{item.label}</Link></div>);
       });
    }

    render() {
        let series = this.props.data.series;
        let body;
       
        let href = series.last_url.split('/');
        body = (
            <div className="card books page left-cover" style={{display:'block'}}>
                <div className="card-content">
                    <div className="col-md-2 col-xs-12 cover">
                        <div className="cover-image-container">
                            <div className="cover-outer-align">
                                <div className="cover-inner-align">
                                    <img className="cover-image"
                                        src={series.thumb_url}/>
                                </div>
                            </div>
                        </div>
                        <div className="source-link" style={{padding: "10px 0"}}>
                            <a href={series.origin} target="_blank" className="btn btn-play"><i className="fa fa-link fa-fw"></i>Source</a>
                        </div>
                    </div>

                    <div className="col-md-10 col-xs-12 detail">
                        <a className="title" href="#">{series.name}</a>

                        <div className="col-xs-12 subtitle-container">
                            <a className="subtitle" href="#">{series.authors}</a>
                        </div>
                        <div className="col-xs-12 alias">{series.aka}</div>
                        <div className="col-xs-12 genres poros">
                            <div className="tengah">
                        {this._renderTags(series.tags)}
                            </div>
                        </div>
                        <div className="col-xs-12 updated">{series.time}</div>
                        <div className="col-xs-12 btn-ch">
                            <Link to="chapter" params={{seriesSlug: href[0], chapterSlug: href[1]}} className="btn btn-play">
                                <i className="fa fa-leanpub fa-fw"></i>
                            {series.last_chapter}</Link>
                        </div>
                        <div className="col-xs-12 description">
                            <p>
                        {series.description}
                            </p>
                        </div>
                    </div>
                </div>
                <div className="title-green" > Chapters </div>
                <ChapterList chapters={series.chapters}/>
            </div>
        );

        return (
            <div className="row">
            <center>
            {body}
            </center>
            </div>
        );
    }
}

Pages.defaultProps = {
    series: {
        "aka": "",
        "authors": [],
        "thumb_url": null,
        "name": "",
        "status": "",
        "description": [],
        "tags": [],
        "site": null,
        "time": null,
        "chapters": []
    }
};

class Series extends Component {
    constructor(props) {
        super(props);
    }

    render() {
        return (
            <div>
                <div className="container">
                
               <Pages {...this.props}/>
                </div>
            </div>
        );
    }
}

Series.fetchData = (token, params, query) => {
    let url = '/series/' + params.seriesSlug;
    return api.post(url, token).then(null ,
        function(){
            return {error: true};
        });
};

export default Series;