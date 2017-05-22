import React, {Component, PropTypes, findDOMNode} from 'react';
import Radium from 'radium';


@Radium.Enhancer
class InfiniteScroll extends Component {
  constructor() {
    super();
    this._lastHeight = 0;
    this._update = this._update.bind(this);
  }

  componentDidMount() {
    this._attachListeners();
  }

  componentWillReceiveProps(nextProps: Object) {
    if (!nextProps.hasMore) {
      this._detachListeners();
    }
  }

  componentWillUnmount() {
    this._detachListeners();
  }

  _attachListeners() {
    window.addEventListener('resize', this._update);
    window.addEventListener('scroll', this._update);
    this._update();
  }

  _detachListeners() {
    window.removeEventListener('resize', this._update);
    window.removeEventListener('scroll', this._update);
  }

  _onScroll(event: Event) {
    this.props.onScroll(event);
    this._update();
  };

  _update() {
    let el = findDOMNode(this);
    let height = el.scrollHeight;
    // ScrollTop + offsetHeight is within threshold of scrollHeight
    let isPastThreshold = (el.scrollHeight -
      el.offsetHeight -
      el.scrollTop
    ) < Number(this.props.threshold);
    
    if ((!this._lastHeight || this._lastHeight < height) && isPastThreshold) {
      // call loadMore after _detachListeners to allow
      // for non-async loadMore functions
      this.props.onRequestMoreItems();
      this._lastHeight = height;
    }
  };

  render(): any {
    let style = this.props.isScrollContainer ? {overflow: 'auto'} : null;
    return (
      <div
        onScroll={this._onScroll.bind(this)}
        style={[this.props.style, style]}>
        {this.props.children}
      </div>
    );
  }
}

InfiniteScroll.propTypes = {
  // Whether or not to listen for scroll and resize events. Set this to `true`
  // when you have loaded all the data already.
  hasMore: PropTypes.bool.isRequired,
  // Called when page is within `threshold` of the bottom.
  onRequestMoreItems: PropTypes.func.isRequired,
  onScroll: PropTypes.func.isRequired,
  threshold: PropTypes.number.isRequired,

  children: PropTypes.node,
  isScrollContainer: PropTypes.bool,
  style: PropTypes.object,
};

InfiniteScroll.defaultProps = {
  hasMore: false,
  isScrollContainer: false,
  onRequestMoreItems: () => {},
  threshold: 250,
};

function getAbsoluteOffsetTop(element) {
  if (!element) {
    return 0;
  }
  return element.offsetTop + getAbsoluteOffsetTop(element.offsetParent);
}

function getWindowScrollTop() {
  if (window.pageYOffset !== undefined) {
    return window.pageYOffset;
  }

  let element: any =
    document.documentElement ||
    document.body.parentNode ||
    document.body;

  return element.scrollTop;
}

export default InfiniteScroll;