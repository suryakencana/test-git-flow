/** @flow */

import React, {Component, PropTypes, findDOMNode } from 'react';
import router from 'utils/router';
import GoogleAnalytics from 'react-g-analytics';
import { connect } from 'react-redux';
import { RouteHandler } from 'react-router';
import { resetErrorMessage, MessageBox, toggleDrawer } from '../actions';
import TransitionGroup from 'react/lib/ReactCSSTransitionGroup';

import MsgBox from 'components/MsgBox';
import Spinner from 'components/SpinnerUI';
import ScrollToTopBtn from 'components/ScrollToTop';
import SideBarUI from 'components/SideBar';

import Sidebar from 'handlers/layouts/Sidebar';
import Navbar from 'handlers/layouts/Navbar';
import Footer from 'handlers/layouts/Footer';

import injectTapEventPlugin from 'react-tap-event-plugin';


injectTapEventPlugin();

class App extends Component {
  constructor(props) {
    super(props);
    this._handleDismissClick = this._handleDismissClick.bind(this);
    this._renderErrorMessage = this._renderErrorMessage.bind(this);
    this._menuButtonClick = this._menuButtonClick.bind(this);
    this._onSetOpen = this._onSetOpen.bind(this);

    this.state = { 
      loading: false,
      genres: undefined,
      docked: false,
      transitions: true,
      touch: true,
      touchHandleWidth: 20,
      dragToggleDistance: 30,
      ismobile: false
    };
  }

  componentDidMount() {
    let timeout;
    this.props.loadingEvents.on('start', () => {
      clearTimeout(timeout);
      timeout = setTimeout(() => {
        this.setState({ loading: true });
      }, 500);
    });
    this.props.loadingEvents.on('end', () => {
      clearTimeout(timeout);
      this.setState({ loading: false });
    });
  }

  componentWillUnmount() {
    clearTimeout(this.pid);
  }

  _onSetOpen(open) {
    this.props.toggleDrawer(open);
  }

  _menuButtonClick(ev) { 
    this._onSetOpen(!this.props.drawerMenu);

    if (ev) {
      ev.preventDefault();
    }
  }

  _renderErrorMessage() {
    const { errorMessage } = this.props;
    if (!errorMessage) {
      return null;
    }

    return (<MsgBox onClick={this._handleDismissClick} 
      log={errorMessage.log} messageText={errorMessage.text} />);
  }

  _handleDismissClick(e) {
    this.props.resetErrorMessage();
  }

  render(): any {    
    let sidebar = <Sidebar {...this.props}/>;
    let sidebarProps = {
      sidebar: sidebar,
      docked: this.state.docked,
      open: this.props.drawerMenu,
      touch: this.state.touch,
      touchHandleWidth: this.state.touchHandleWidth,
      dragToggleDistance: this.state.dragToggleDistance,
      transitions: this.state.transitions,
      onSetOpen: this._onSetOpen,
    };
    let contentHeader = (
      <span>
      {!this.state.docked &&
       <a className="menu-trigger" onClick={this._menuButtonClick} href="#"> <i className="fa fa-bars fa-fw"></i></a>}
       </span>);

    let body = (
      <div className="body">
      <Navbar menuBar={contentHeader}/>
      {this.state.loading ? <Spinner /> : null}
      <div className="content-wrapper">
      {this._renderErrorMessage()}
      <GoogleAnalytics id="UA-65629589-1" />
      <TransitionGroup transitionName="tcontent">
      <RouteHandler key={name} {...this.props} />
      </TransitionGroup>
      </div>
      <Footer />
      <ScrollToTopBtn />
      </div>
      );
    return (
      <SideBarUI {...sidebarProps}>
      {body}
      </SideBarUI>
      );
  }
}

function mapStateToProps(state) {
  return {
    editors: state.editors,
    errorMessage: state.errorMessage,
    drawerMenu: state.drawerMenu
  }
}

export default connect(
  mapStateToProps,
  { resetErrorMessage, MessageBox, toggleDrawer }
  )(App);