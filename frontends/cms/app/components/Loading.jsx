var React = require("react");
module.exports = React.createClass({
    css: {
        'textAlign': 'center',
        'marginTop': '30px'
    },
    render: function(e) {
        if (this.props.hasOwnProperty('loading') &&
            this.props.loading === false) {
            return null;
        }

        var text = <h4>{this.props.text}</h4> || '';
        return (
            <div className='icon-container' style={this.css}>
                <i className='fa fa-5x fa-spinner fa-pulse'></i>
                {text}
            </div>
        );
    }
});