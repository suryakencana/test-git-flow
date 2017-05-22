/** @flow */

import React from 'react';
import { Route, DefaultRoute, NotFoundRoute } from'react-router';
import App from 'handlers';
import Index from 'handlers/Home';
import Popular from 'handlers/Popular/wrapper';
import Latest from 'handlers/Latest/wrapper';
import Series from 'handlers/Series';
import Chapter from 'handlers/Chapter';
import Search from 'handlers/Search';
import Genre from 'handlers/Genre';

module.exports = () => {
    return [
    <Route name="root" path="/" handler={App}>
        <DefaultRoute name="home" handler={Index} />
        <Route name="popular" path="/popular" handler={Popular} />
        <Route name="latest" path="/latest" handler={Latest} />
        <Route name="series" path="/manga/:seriesSlug" handler={Series} />
        <Route name="chapter" path="/chapter/:seriesSlug/:chapterSlug" handler={Chapter} />
        <Route name="search" path="/search/:q" handler={Search} />
        <Route name="genre" path="/genre/:q" handler={Genre} />
    </Route>
    ];
};