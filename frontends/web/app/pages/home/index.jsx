var React = require('react');
var _ = require('lodash');
var HeadRender = require('components/mixin/HeadRender');
var Tabs = require('components/Tabs');
var Radium = require('radium');
var Banner = require('pages/home/slickers');
var Latest = require('pages/home/latest');
var LatestIndex = require('pages/mobiles/latest');
var Popular = require('pages/home/popular');
var PopularIndex = require('pages/mobiles/popular');

var Twitter = require('components/socials/Twitter');
var Facebook = require('components/socials/Facebook');
var GooglePlus = require('components/socials/GooglePlus');

var isMobile = require('utils/ismobile');

var Homepage = React.createClass({
    mixins: [HeadRender],
    propTypes: {
        initLoaded: React.PropTypes.bool
    },

    getInitialState: function () {
        return {
            initLoaded: false
        };
    },

    componentDidUpdate(){},

    componentDidMount(){
        this.setState({
            head: {
                title: "Niimanga - The only manga reader page you'll ever need",
                description: "Niimanga - Manga reader for free and enjoying what you'll need to reading manga popular series",
                sitename: "Niimanga",
                image: "http://niimanga.net/static/res/share.png",
                url: "http://niimanga.net"
            }
        });        
    },

    componentWillUnmount(){
        this.setState({initLoaded: false});
    },

    render: function() {
        return (<span>
            { isMobile()? (<center><Banner /></center>): null}
            <div className="container header-wrapper">
            {this.renderHead()}
            { isMobile()? null: (<span>
            <a ref="ad-left" href="#"><div style={styles.left}></div></a>
            <a ref="ad-right" href="#"><div style={styles.right}></div></a>
            </span>)
            }

            <div className="row">
            <div className="col-xs-12 col-md-9">
                
                {isMobile()? (
                <Tabs>
                    <Tabs.Panel className="btn btn-play" title='Hot'>
                      <PopularIndex {...this.props} />
                    </Tabs.Panel>
                    <Tabs.Panel title='Release'>
                      <LatestIndex {...this.props} />
                    </Tabs.Panel>
                </Tabs>): (<span><Banner/><Latest {...this.props}/></span>)}
            </div>

            <div className="col-xs-12 col-md-3">
                <center>
                <div className="g-page" 
                        data-width={!isMobile()? "225": "275" } 
                        data-href="//plus.google.com/u/0/109363191390818524400" 
                        data-rel="publisher">
                </div>

                {!isMobile()?<Popular {...this.props}/>: null }
                
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
                            data-width ={!isMobile()? "225": "275" }
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
           </span> );
}
});

var styles = {
    left: {
        height: '900px',
        left: '-493px',
        top: '34px',
        position: 'fixed',
        width: '50%',
        cursor: 'pointer',
        background: 'url(/static/res/ad-banner-left.png) 100% 0% no-repeat scroll transparent'
    },

    right: {
        height: '900px',
        left: '711px',
        top: '34px',
        position: 'fixed',
        width: '50%',
        cursor: 'pointer',
        background: 'url(/static/res/ad-banner-right.png) 100% 0% no-repeat scroll transparent'
    }
};

module.exports = Homepage;