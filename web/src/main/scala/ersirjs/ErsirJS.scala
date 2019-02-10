package ersirjs

import ersir.shared._
import ersirjs.render.Index
import loci.communicator.ws.akka.WS
import loci.registry.Registry
import loci.transmitter.RemoteRef
import org.scalajs.dom
import rescala.default._
import rescala.rescalatags._
import scalatags.JsDom.implicits.stringFrag
import scalatags.JsDom.tags.body
import scala.collection.mutable

import scala.concurrent.Future
import scala.scalajs.concurrent.JSExecutionContext.Implicits.queue
import scala.scalajs.js
import scala.scalajs.js.annotation.JSImport

@JSImport("mqtt", JSImport.Namespace)
@js.native
object mqtt extends js.Object {
  def connect(i: String): js.Dynamic = js.native
}

object ReMqtt {
  println(s"initializing mqtt …")
  val connection: js.Dynamic = mqtt.connect("ws://127.0.0.1:9001")
  val topics: mutable.Map[String, Evt[String]] = mutable.Map[String, Evt[String]]()
  connection.on("message", { (topic: String, message: js.Dynamic) =>
    topics.get(topic).foreach(e => e.fire(message.toString))
  })
  println(s"mqtt initialized")


  def topicstream(topic: String): Evt[String] = {
    topics.getOrElseUpdate(topic, {
      println(s"subscribing to mqtt topic $topic")
      connection.subscribe(topic)
      println(s"subscribed to $topic")
      Evt[String]
    })
  }
}


object ErsirJS {

  val wsUri: String = {
    val wsProtocol = if (dom.document.location.protocol == "https:") "wss" else "ws"
    s"$wsProtocol://${dom.document.location.host}${dom.document.location.pathname}ws"
  }

  def main(args: Array[String]): Unit = {
    println("initing")
    dom.document.body = body("loading data …").render


    val registry = new Registry
    val connection: Future[RemoteRef] = registry.connect(WS(wsUri))
    println(s"waiting for ws connection to server …")
    connection.foreach { remote =>
      val descriptionsCRDT = registry.lookup(Bindings.crdtDescriptions, remote)
      println(s"requesting $descriptionsCRDT")
      descriptionsCRDT.failed.foreach{ t =>
        t.printStackTrace()
      }
      descriptionsCRDT.foreach { res =>
        val descriptions = res.valueSignal

        val emergencies = Future { ReMqtt.topicstream("city/alert_state") }


        emergencies.foreach(_.observe{ str =>
          res.append(str)
        })

        val manualStates = Evt[AppState]()

        val actions = new Actions(manualStates = manualStates)
        val index = new Index(actions, descriptions)
        val app = new ReaderApp()

        app.makeBody(index, manualStates).asFrag.applyTo(dom.document.body.parentElement)
      }
    }
  }

}
