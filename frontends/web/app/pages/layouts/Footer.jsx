var React = require('react'),
    Router = require('react-router'),
    { Route, DefaultRoute, RouteHandler, Link } = Router;

module.exports = React.createClass({
    render: function() {
        return (
            <footer className="footer-wrapper">
                <div className="container">
                    <div className="row">
                        <div className="col-md-12 footer-main">
                            <ul className="sitemap">
                                <li><Link to="/">home</Link></li>
                                <li><Link to="popular">hot manga</Link></li>
                                <li><Link to="latest">latest manga</Link></li>

                            </ul>
                        </div>
                    </div>
                    <div className="row">
                        <div className="col-md-12 disclaimer">
                            Copyrights and trademarks for the manga, and other promotional materials are held by their respective owners and their use is allowed under the fair use clause of the
                            Copyright Law.
                            <div className="corporate">© 2015 Niimanga.net.</div>
                        </div>
                    </div>
                </div>
            </footer>
        );
    }
});