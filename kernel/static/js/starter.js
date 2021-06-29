//
document.addEventListener("DOMContentLoaded", function(){
  // Handler when the DOM is fully loaded
  if ( document.documentMode || document.attachEvent )    {
    document.querySelector( 'html' ).classList.add( 'ie' );
  }
//  screensize info ( used during development )
  var hw = "" + document.body.clientHeight
         + "," + document.body.clientWidth + "";
  var sty ="position:absolute; top:0; right:0; z-index:99;"
          + "background-color:white; color:black; font-size:small;"
          + "border-bottom: thin solid silver;"
          + "border-left: thin solid silver;"
          + "display: none;";
  var box = document.createElement("div");
  box.setAttribute("id","sizeBox");
  box.setAttribute("style",sty);
  box.appendChild(document.createTextNode(hw));
  document.body.appendChild(box);
  window.addEventListener("resize", function(){
    let box = document.querySelector("#sizeBox");
    box.childNodes[0].data = "" + document.body.clientHeight
                           + "," + document.body.clientWidth + "";
  });
//
  var btn = document.querySelector('#user_menu');
  if ( btn ) {
    btn.addEventListener("click", function(){
      this.parentElement.querySelector('ul').classList.toggle('hidden');
      return;
    })
  }
});
