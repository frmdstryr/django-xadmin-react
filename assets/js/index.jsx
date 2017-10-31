import React from 'react';
import ReactDOM from 'react-dom';
import moment from 'moment';

class ModalList extends React.Component {
  constructor(props) {
    super(props);
    this.connect();
    this.state = {
      headers: [],
      objects: [],
      seconds: 0,
      connected: false,
    };
  }

  connect() {
     let scheme = (window.location.protocol=="https:")?"wss":"ws";
     let url = `${scheme}://${window.location.host}/live/`;
     this.ws = new WebSocket(url);
     this.ws.onopen = (e)=>this.onOpen(e);
     this.ws.onmessage= (e)=>this.onMessage(e);
     this.ws.onclose = (e)=>this.onClose(e);
  }

  onOpen(e) {
    let ws = this.ws;
    ws.send(JSON.stringify({
      path:window.location.pathname,
      type:'get'
    }));
    this.setState({connected:true});
  }

  onClose(e) {
    this.setState({connected:false});
    this.connect();
  }

  /**
   * Handle a message from the server
   */
  onMessage(e) {
    console.log(e);
    let data = JSON.parse(e.data);
    console.log("Received", data);
    this.setState(data);

    // Refresh
    try{
      $('.editable-handler').editpop();
    } catch (e) {
      // dilligaf
    }
  }

  /**
   * Send a message for the server to handle
   */
  sendMessage(data) {
    if (!this.ws) {
      return
    }
    let ws = this.ws;
    let msg = JSON.stringify({
      path:window.location.pathname,
      message:data,
    })
    console.log("Sending", msg);
    ws.send(msg);
  }

  /**
   * Update our times every second
   */
  tick() {
    this.setState((prevState) => ({
      seconds: prevState.seconds + 1
    }));
  }

  componentDidMount() {
    this.interval = setInterval(() => this.tick(), 1000);
  }

  renderHeader(h) {
    return h;
  }

  renderCell(f,j) {
    if (f.type=='fromNow') {
      // Render eta
      return moment(f.value).fromNow();
    } else if (f.type=='date') {
            // Render eta
      return moment(f.value).calendar();
    } else if (f.type=='action') {
        // Render an action button
        return <button className={f.class} onClick={(e)=>{
          e.preventDefault();
          this.sendMessage(f.url);
          }}>{f.text}</button>;
    } else if (f===true||f===false) {
      // Render boolean
      return <i className={"fa fa"+ (f?"-check-circle text-success":"-times-circle")} alt={`${f}`} />;
    } else if (f.type=='editable') {
      return <div>
          <div className="btn-group pull-right">
            <a className="editable-handler" title=""
                  data-editable-field={f.field}
                  data-editable-loadurl={f.url}
                  data-original-title={"Enter "+f.field}>
                  <i className="fa fa-edit"></i>
            </a>
          </div>
          <span className="editable-field">{f.value}</span>
      </div>;
    }
    return f;
  }

  render() {
    let headers = this.state.headers;
    let objects = this.state.objects;
    if (!this.state.connected) {
      return <div className="alert alert-warning" style={{marginTop:70}} role="alert">
        <b>Connecting... Please wait.</b><br />
        If this does not go away please request help at <a href="mailto:dev@smirta.com">dev@smirta.com</a>
      </div>;

    }
    return (
      <table className="table table-bordered table-striped table-hover">
       <thead>
          <tr>
             {headers.map((h,j)=>
               <th key={j}>{this.renderHeader(h)}</th>
             )}
          </tr>
       </thead>
       <tbody>
        {objects.map((obj,i)=>
          <tr className="grid-item" key={i}>
              {obj.map((f,j)=>
                <td key={j}>{this.renderCell(f,j)}</td>
              )}
          </tr>
        )}
        </tbody>
      </table>
    );
  }
}


ReactDOM.render(<ModalList />,document.getElementById('results-list'));
