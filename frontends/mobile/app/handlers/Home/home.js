/** @flow */

import React, { Component, PropTypes, findDOMNode} from'react';
import Radium from 'radium';

import _ from 'lodash';
import api from 'utils/api';
import cache from 'utils/cache';
import LoadingUI from 'components/LoadingUI';
import Tabs from 'components/Tabs';

import Banner from './slickers';
import Latest from 'handlers/Latest';
import Popular from 'handlers/Popular';

import Twitter from 'components/socials/Twitter';
import Facebook from 'components/socials/Facebook';
import GooglePlus from 'components/socials/GooglePlus';


class Home extends Component {
    constructor(props) {
        super(props);
    }

    render(): any {
        return (<span>
            <center><Banner /></center>
            <div className="container header-wrapper">

            <div className="row">
            <div className="col-xs-12">
                <Tabs>
                    <Tabs.Panel className="btn btn-play" title='Hot'>
                      <Popular {...this.props} />
                    </Tabs.Panel>
                    <Tabs.Panel title='Release'>
                      <Latest {...this.props} />
                    </Tabs.Panel>
                </Tabs>
            </div>

            <div className="col-xs-12">
                <center>
                <div className="g-page" 
                        data-width="275"
                        data-href="//plus.google.com/u/0/109363191390818524400" 
                        data-rel="publisher">
                </div>
                
                <div className="title-green">Social Media Share</div>
                <Twitter type="share" url="http://www.niimanga.net" text="Easy for read manga #niimanga #manga @niimanga"/>
                <Facebook type="share" cleanup={true} url="http://www.niimanga.net" text="Easy for read manga #niimanga #manga @niimanga"/>
                <GooglePlus type="share" url="http://www.niimanga.net" text="Easy for read manga #niimanga #manga @niimanga"/>
                
                <div className="socmed col-xs-6">
                    <div className="socmed col-xs-6 fb-like" 
                    data-href="https://www.facebook.com/niimanga" 
                    data-layout="button_count" 
                    data-action="like" 
                    data-show-faces="true" 
                    data-share="false">
                    </div>
                </div>
                <div className="socmed col-xs-6"><div className="fb-share-button" data-href="http://www.niimanga.net" data-layout="button_count"></div></div>
                <div className="socmed col-xs-6"><div className="g-plusone" data-annotation="bubble" data-href="http://www.niimanga.net"></div></div>
                <div className="socmed col-xs-6"><div className="g-follow" data-annotation="bubble" data-height="20" data-href="//plus.google.com/u/0/109363191390818524400" data-rel="publisher"></div></div>

                <div className="socmed">
                    <a className="twitter-timeline card-content" 
                    href="https://twitter.com/niimanga"
                    data-widget-id="625868171711393792">Tweets by @niimanga</a>
                </div>

                <div className="socmed">
                    <div className="fb-page"
                            data-width ="275"
                            data-href="https://www.facebook.com/niimanga" 
                            data-small-header="false" 
                            data-adapt-container-width="true" 
                            data-hide-cover="false" 
                            data-show-facepile="true" 
                            data-show-posts="true">
                        <div className="fb-xfbml-parse-ignore">
                        <blockquote cite="https://www.facebook.com/niimanga">
                        <a href="https://www.facebook.com/niimanga">Niimanga</a></blockquote>
                        </div>
                    </div>
                </div>
                </center>
            </div>
        </div>
    </div>
    </span>);
    }
}

export default Home;