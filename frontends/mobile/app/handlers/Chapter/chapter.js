/** @flow */

import React, { Component, PropTypes, findDOMNode} from'react';
import { Link } from 'react-router';
import _ from 'lodash';
import api from 'utils/api';
import cache from 'utils/cache';
import LoadingUI from 'components/LoadingUI';


class Pages extends Component {
    constructor() {
        super();
        this.NUM_CONCURRENT = 3;  // Max number of pages to load concurrently
        this.state = {
             loaded: []
        }
    }

    componentWillReceiveProps(nextProps) {

        if (nextProps.imgs.length > 0) {

            // Leave pages as-is if already rendered
            let loaded = this.state.loaded;
            if (loaded.length > 0 && loaded[0] === nextProps.imgs[0]) {
                return;
            }

            // Render first image which has an onLoad event handler which
            // renders the second image which has an onload event handler to
            // render the third image... and so on.
            this.setState({
                loaded: nextProps.imgs.slice(0, this.NUM_CONCURRENT)
            });

        } else {
            // Clean up when changed to another chapter
            this.setState({
                loaded: []
            });
        }
    }

    render() {
        let all = this.props.imgs;
        let loaded = this.state.loaded;
        let self = this;

        let images = loaded.map(function (url, index) {

            // function to append the next NUM_CONCURRENT images into the DOM
            // when this image has finished loading:
            let appendFunc = function () {
                for (let i = 1, len = self.NUM_CONCURRENT; i <= len; i++) {
                    let nextIndex = index + i;
                    let nextImgUrl = all[nextIndex];

                    if (nextIndex < all.length) {
                        if (loaded.indexOf(nextImgUrl) === -1) {
                            loaded.push(nextImgUrl);
                        }
                    } else {
                        break;
                    }
                }

                self.setState({loaded: loaded});
            };
            return (
                <div className="col-xs-12 col-md-12 col-sm-12">
                  
                    <div className="card-content" style={{marginBottom: '10px'}}>
                        <img style={{display:'block', width:'100%', height:'auto'}} key={url + index} src={url}
                            onLoad={appendFunc} />
                        <div className="page-number">{ index + 1 } / { all.length }</div>
                    </div>
                  
                </div>
            );
        });
        return (
            <div className="chapter-image">
                {images}
                <LoadingUI loading={all.length > loaded.length} />
            </div>
        );
    }
}

Pages.propTypes = {
    imgs: PropTypes.array
};

class ActionBar extends Component {
    render(): any {
        let prevBtn, nextBtn, seriesBtn;

        let info = this.props.info;
        let prev = info.prev_chapter_url;
        let next = info.next_chapter_url;
        let series = info.series_url;

        if (prev !== null) {
            //prev = '/chapter/' + encodeURIComponent(prev);
            prevBtn = (
                <a href={prev} className="btn btn-primary" id="prev-btn">
                    <i className="fa fa-lg fa-angle-double-left fa-fw"></i> prev
                </a>
            );
        }

        if (next !== null) {
            //next = '/chapter/' + encodeURIComponent(next);
            nextBtn = (
                <a href={next} className="btn btn-primary" id="next-btn">
                    next
                    <i className="fa fa-lg fa-angle-double-right fa-fw"></i>
                </a>
            );
        }

        seriesBtn = (
            <Link to="series" params={{seriesSlug: series}} className="btn btn-info" id="chapter-list-btn">
                <i className="fa fa-lg fa-angle-double-up fa-fw"></i> chapter_list
            </Link>
        );

        return (
            <div className="chapter-navs  btn-group">
                {prevBtn} {seriesBtn} {nextBtn}
            </div>
        );
    }
}

ActionBar.propTypes = {
    info: PropTypes.object,
    setState: PropTypes.object
}

class Chapters extends Component {
    constructor() {
        super();
        this.state = {
            info: {
                pages: [],
                name: '',
                series_url: '',
                next_chapter_url: null,
                prev_chapter_url: null
            },
            fetching: true,
            processingBookmark: false
        };

        this.fetchPages = this.fetchPages.bind(this);
        this.updateChapterData = this.updateChapterData.bind(this);
    }

    componentDidMount() {
        let data = this.props.data.chapter;
        data.error ? this.setState({fetching: false}): this.fetchPages(data);
    }

    render(): any {
        let data = this.props.data.chapter;
        let info = this.state.info,
            name = info.name,
            next = info.next_chapter_url,
            prev = info.prev_chapter_url,
            fetching = this.state.fetching;

        let pages = <Pages imgs={info.pages} />;

        let setState = this.setState.bind(this);

        let body;

        data.error ? this.props.MessageBox('There some image cannot be loaded for this chapter'): null;

        return (
            <div className="container">
                <div className="row">
                { 
                    data.error ? null : (
                    <center>
                        <h2 className="chapter-name">{name}</h2>

                        <ActionBar info={info}  setState={setState} />
                        <LoadingUI loading={fetching} />
                    {pages}
                        <ActionBar info={info} setState={setState} />
                    </center>
                )}
                </div>
            </div>
        );
    }

    fetchPages(data) {
        let newState = this.state;
        newState.cards = [],
        newState.fetching = true;
        this.setState(newState);
        this.updateChapterData(data);
    }

    updateChapterData(data) {
        this.setState({
            info: data,
            fetching: false
        });
    }
}

Chapters.fetchData = (token, params, query) => {
    let url = '/chapter/' + params.seriesSlug + '/' + params.chapterSlug;
    return api.post(url, token).then(null ,
        function(){
            return {error: true};
        });
};

export default Chapters;